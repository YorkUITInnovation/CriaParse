from io import BytesIO
from typing import List

from fastapi import UploadFile

from criaparse.parser import Parser, Element
from criaparse.parsers.alsyllabus.conversions import run_converter


class AlSyllabusParser(Parser):
    """
    Al Syllabus parser
    """

    def accepted_mimetypes(self) -> List[str]:
        """
        Empty list of accepted mimetypes (all)
        :return: List of allowed mimetypes

        """

        return ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    async def _parse(self, file: UploadFile, **kwargs) -> List[Element]:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

        parsed_elements: List[Element] = run_converter(
            docx=self.to_buffer(file=file)
        )

        return parsed_elements
