import time
from typing import List

from fastapi import UploadFile

from criaparse.daemon.job import Job
from criaparse.parser import Parser
from criaparse.models import Element, ParserResponse, ParserFile, ParserStrategy
from criaparse.parsers.alsyllabusfr.conversions import run_converter


class AlSyllabusParserFr(Parser):
    """
    Al Syllabus parser
    """

    @classmethod
    def strategy(cls) -> ParserStrategy:
        return ParserStrategy.AL_SYLLABUS_FR

    @classmethod
    def step_count(cls, **kwargs) -> int:
        return 1

    def accepted_mimetypes(self) -> List[str]:
        """
        Empty list of accepted mimetypes (all)
        :return: List of allowed mimetypes

        """

        return ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    async def _parse(self, file: ParserFile, job: Job, **kwargs) -> ParserResponse:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

        start_time = time.time()

        parsed_elements: List[Element] = run_converter(
            docx=file.buffer
        )

        end_time = time.time()

        await job.set_step_finished("Parsing", 1, (end_time - start_time))

        return ParserResponse(elements=parsed_elements)
