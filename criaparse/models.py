from __future__ import annotations

import enum
import importlib
import io
import typing
import uuid
from io import BytesIO
from typing import List, Generator

from pydantic import BaseModel, Field, PrivateAttr
from starlette.datastructures import UploadFile

if typing.TYPE_CHECKING:
    from criaparse.parser import Parser


class ParserFile(BaseModel):
    """
    A file to be parsed

    """

    filename: str
    content_type: str
    filedata: bytes

    _buffer: io.BytesIO | None = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._buffer = None

    @property
    def buffer(self) -> io.BytesIO:
        """Convert the filedata to a BytesIO buffer"""

        if self._buffer:
            self._buffer.seek(0)
            return self._buffer

        buffer = BytesIO()
        buffer.write(self.filedata)
        buffer.seek(0)

        self._buffer = buffer
        return self._buffer

    @classmethod
    async def from_upload_file(cls, upload_file: UploadFile) -> "ParserFile":
        return cls(
            filename=upload_file.filename,
            content_type=upload_file.content_type,
            filedata=await upload_file.read()
        )


class ElementType(enum.Enum):
    """
    The type of element

    """

    FIGURE_CAPTION = "FigureCaption"
    NARRATIVE_TEXT = "NarrativeText"
    LIST_ITEM = "ListItem"
    TITLE = "Title"
    ADDRESS = "Address"
    TABLE = "Table"
    PAGE_BREAK = "PageBreak"
    HEADER = "Header"
    FOOTER = "Footer"
    UNCATEGORIZED_TEXT = "UncategorizedText"
    IMAGE = "Image"
    FORMULA = "Formula"

    # Custom
    UNKNOWN = "Unknown"
    TABLE_ENTRY = "TableEntry"

    BACKWARDS_COMPATIBLE_ASSET_CONTAINER = "BackwardsCompatibleAssetContainer"

    @classmethod
    def of(cls, value: str) -> "ElementType":
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


class ParserStrategy(str, enum.Enum):
    """Map of parser strategies"""

    GENERIC = "GENERIC"
    AL_SYLLABUS = "ALSYLLABUS"
    AL_SYLLABUS_FR = "ALSYLLABUSFR"
    PARAGRAPH = "PARAGRAPH"

    def create(self) -> "Parser":
        parser_classes = {
            self.GENERIC: "criaparse.parsers.generic.generic.GenericParser",
            self.AL_SYLLABUS: "criaparse.parsers.alsyllabus.alsyllabus.AlSyllabusParser",
            self.AL_SYLLABUS_FR: "criaparse.parsers.alsyllabusfr.alsyllabusfr.AlSyllabusParserFr",
            self.PARAGRAPH: "criaparse.parsers.paragraph.paragraph.ParagraphParser"
        }

        module_path, class_name = parser_classes[self].rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)()

    @classmethod
    def iterator(cls) -> Generator["ParserStrategy", None, None]:
        """Iterate over the parser strategies"""
        for strategy in cls:
            yield strategy


class Asset(BaseModel):
    """
    An asset extracted from the document

    """

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_mimetype: str
    data_base64: str


class Element(BaseModel):
    type: ElementType
    text: str
    metadata: dict = Field(default_factory=dict)
    element_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ParserResponse(BaseModel):
    elements: List[Element]
    assets: List[Asset] = Field(default_factory=list)


class FileUnsupportedParseError(RuntimeError):
    """
    Thrown when someone tries to parse a file not supported by a parser

    """
