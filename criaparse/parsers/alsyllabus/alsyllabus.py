from typing import List

from fastapi import UploadFile

from criaparse.parser import Parser
from criaparse.models import ElementType, Element, ParserResponse
from criaparse.parsers.alsyllabus.al_types import AlNode
from criaparse.parsers.alsyllabus.conversions import convert_file


class AlSyllabusParser(Parser):
    """
    Al Syllabus parser
    """

    @classmethod
    def step_count(cls) -> int:
        return 1

    @classmethod
    def parser_name(cls) -> str:
        return "ALSYLLABUS"

    def accepted_mimetypes(self) -> List[str]:
        """
        Empty list of accepted mimetypes (all)
        :return: List of allowed mimetypes

        """

        return ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    async def _parse(self, file: UploadFile, **kwargs) -> ParserResponse:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

        al_nodes: List[AlNode] = convert_file(
            file_bytes=self.to_buffer(file=file)
        )

        elements: List[Element] = []
        for node in al_nodes:
            elements.append(
                Element(
                    type=ElementType.of(node['type']),
                    text=node['text'],
                    metadata=node['metadata']
                )
            )

        return ParserResponse(elements=elements)
