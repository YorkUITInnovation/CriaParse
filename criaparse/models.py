import enum
import uuid
from typing import List

from pydantic import BaseModel, Field


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
