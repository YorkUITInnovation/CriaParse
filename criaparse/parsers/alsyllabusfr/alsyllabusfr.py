import time
from typing import List

from fastapi import UploadFile

from criaparse.daemon.job import Job
from criaparse.parser import Parser
from criaparse.models import Element, ParserResponse
from criaparse.parsers.alsyllabusfr.conversions import run_converter


class AlSyllabusParserFr(Parser):
    """
    Al Syllabus parser
    """

    @classmethod
    def name(cls) -> str:
        return "ALSYLLABUSFR"

    @classmethod
    def step_count(cls) -> int:
        return 1

    def accepted_mimetypes(self) -> List[str]:
        """
        Empty list of accepted mimetypes (all)
        :return: List of allowed mimetypes

        """

        return ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    async def _parse(self, file: UploadFile, job: Job, **kwargs) -> ParserResponse:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

        start_time = time.time()

        parsed_elements: List[Element] = run_converter(
            docx=self.to_buffer(file=file)
        )

        end_time = time.time()

        await job.set_step_finished(0, "Parsing", (end_time - start_time))

        return ParserResponse(elements=parsed_elements)
