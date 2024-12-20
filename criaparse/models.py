from __future__ import annotations

import enum
import importlib
import typing
import uuid
from typing import List, Generator

from pydantic import BaseModel, Field

if typing.TYPE_CHECKING:
    from criaparse.parser import Parser


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
