from typing import List

from criaparse.models import ElementType, Element, ParserResponse, ParserFile, ParserStrategy
from criaparse.parser import Parser
from criaparse.parsers.alsyllabus.al_types import AlNode
from criaparse.parsers.alsyllabus.conversions import convert_file


class AlSyllabusParser(Parser):
    """
    Al Syllabus parser
    """

    @classmethod
    def step_count(cls, **kwargs) -> int:
        return 1

    @classmethod
    def strategy(cls) -> str:
        return ParserStrategy.AL_SYLLABUS

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

        al_nodes: List[AlNode] = convert_file(
            file_bytes=file.buffer
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


__all__ = ["AlSyllabusParser"]
