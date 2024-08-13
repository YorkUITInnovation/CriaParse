import dataclasses
import enum
import io
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import List, BinaryIO

from fastapi import UploadFile


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


@dataclass()
class Element:
    type: ElementType
    text: str
    metadata: dict = dataclasses.field(default_factory=dict)
    element_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))


class FileUnsupportedParseError(RuntimeError):
    """
    Thrown when someone tries to parse a file not supported by a parser

    """


class Parser(ABC):
    """
    Abstract parser implementation

    """

    @abstractmethod
    def accepted_mimetypes(self) -> List[str]:
        """
        List of mimetypes the parser is capable of handling

        :return: Mimetype list

        """

        raise NotImplementedError

    def supports_file(self, file: UploadFile) -> bool:
        """
        Whether the parser supports a specific file

        :param file: The file to check
        :return: Whether it can be parsed by the given parser

        """

        return file.content_type in self.accepted_mimetypes()

    @abstractmethod
    async def _parse(self, file: UploadFile, **kwargs) -> List[Element]:
        """
        Parse a document with the parser

        :return: The parsed element list

        """

        raise NotImplementedError

    def to_buffer(self, file: UploadFile) -> io.BytesIO:
        file: BinaryIO = file.file
        file.seek(0)
        io: BytesIO = BytesIO()
        io.write(file.read())

        return io

    async def parse(self, file: UploadFile, **kwargs) -> List[Element]:
        """
        Parse a document with the parser

        :return: The parsed element list

        """

        if not self.supports_file(file=file):
            raise FileUnsupportedParseError(
                f"The file content type {file.content_type} is not supported by {type(self)}"
            )

        return await self._parse(file=file, **kwargs)
