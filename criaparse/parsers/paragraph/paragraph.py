from typing import List

from criaparse.models import Element, ParserResponse, ParserFile, ParserStrategy, ElementType
from criaparse.parser import Parser
from criaparse.parsers.paragraph.conversions import run_converter


class ParagraphParser(Parser):
    """
    Paragraph parser
    """

    @classmethod
    def step_count(cls, **kwargs) -> int:
        return 1

    @classmethod
    def strategy(cls) -> str:
        return ParserStrategy.PARAGRAPH

    def accepted_mimetypes(self) -> List[str]:
        """
        Supported mimetypes for this parser.
        """

        return [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/markdown",
            "text/plain",
        ]

    async def _parse(self, file: ParserFile, **kwargs) -> ParserResponse:
        """
        Parse the file into paragraph-level elements.

        DOCX files are handled via the existing converter. For simple text
        formats (markdown / plain text) we fall back to a lightweight
        splitter that groups text into paragraph-sized chunks.
        """

        if file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            parsed_elements: List[Element] = run_converter(
                docx=file.buffer
            )
            return ParserResponse(elements=parsed_elements)

        # Fallback for text-like inputs (e.g., markdown / plain text)
        raw_bytes = file.buffer.read()
        try:
            text = raw_bytes.decode("utf-8", errors="ignore")
        finally:
            # Ensure buffer can be reused by any downstream code if needed
            file.buffer.seek(0)

        # Naive paragraph splitter: split on blank lines, then trim.
        paragraphs: List[str] = []
        current: List[str] = []

        for line in text.splitlines():
            if line.strip():
                current.append(line.rstrip())
            elif current:
                paragraphs.append("\n".join(current).strip())
                current = []

        if current:
            paragraphs.append("\n".join(current).strip())

        elements: List[Element] = [
            Element(
                type=ElementType.NARRATIVE_TEXT,
                text=p,
                metadata={"filetype": file.content_type},
            )
            for p in paragraphs if p
        ]

        return ParserResponse(elements=elements)
