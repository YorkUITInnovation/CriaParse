from typing import List

from criaparse.models import Element, ParserResponse, ParserFile
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
    def name(cls) -> str:
        return "PARAGRAPH"

    def accepted_mimetypes(self) -> List[str]:
        """
        Empty list of accepted mimetypes (all)
        :return: List of allowed mimetypes

        """

        return ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    async def _parse(self, file: ParserFile, **kwargs) -> ParserResponse:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

        parsed_elements: List[Element] = run_converter(
            docx=file.buffer
        )

        return ParserResponse(elements=parsed_elements)
