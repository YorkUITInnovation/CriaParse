import asyncio
import logging
import traceback
from typing import Dict, List, Type, Literal

from CriadexSDK import CriadexSDK
from fastapi import UploadFile
from redis.asyncio import Redis

from criaparse.job import Job
from criaparse.models import Element, ParserResponse
from criaparse.parser import Parser
from criaparse.parsers.alsyllabus.alsyllabus import AlSyllabusParser
from criaparse.parsers.alsyllabusfr.alsyllabusfr import AlSyllabusParserFr
from criaparse.parsers.generic.errors import JobNotFoundError
from criaparse.parsers.generic.generic import GenericParser
from criaparse.parsers.paragraph.paragraph import ParagraphParser


class UnsupportedParser(RuntimeError):
    """
    Parser not found or enabled on the server-side

    """


ParseStrategy: Type = Literal["GENERIC", "ALSYLLABUS", "PARAGRAPH", "ALSYLLABUSFR"]


class CriaParse:
    """
    Wrapper for interacting with parsing strategies from FastAPI interface

    """

    def __init__(
            self,
            criadex: CriadexSDK,
            redis: Redis,
    ):
        """
        Initialize the parsers

        :param criadex: Needed to authenticate
        :param redis: Pool to store job results

        """

        self._criadex: CriadexSDK = criadex

        self.parsers: Dict[ParseStrategy, Parser] = {
            "GENERIC": GenericParser(),
            "ALSYLLABUS": AlSyllabusParser(),
            "ALSYLLABUSFR": AlSyllabusParserFr(),
            "PARAGRAPH": ParagraphParser()
        }

        self._redis: Redis = redis
        self._jobs: Dict[str, Job] = {}
        self._loop_task: asyncio.Task = asyncio.create_task(self.handle_jobs())

    async def handle_jobs(self) -> None:

        while True:

            for job_id, job in self._jobs.items():
                if job.expired:
                    del self._jobs[job_id]

            await asyncio.sleep(1)

    @property
    def parsing_strategies(self) -> List[str]:
        """
        List the available parsing strategies
        :return: The list of available parsing strategies

        """

        return list(self.parsers.keys())

    async def parse(
            self,
            file: UploadFile,
            strategy: ParseStrategy = "GENERIC",
            **kwargs
    ) -> ParserResponse:
        """
        Parse a document using the CriaParse suite

        :param file: The file to parse
        :param strategy: The parsing strategy to use
        :return: The parsed file

        """

        # Parse the file
        job = await self.queue_parse(file=file, strategy=strategy, **kwargs)
        await job.future

        # Grab results immediately
        await asyncio.sleep(1)

        # Get result to clear
        return await job.get_result()

    async def queue_parse(
            self,
            file: UploadFile,
            strategy: ParseStrategy = "GENERIC",
            **kwargs
    ) -> Job:
        """
        Queue a parse job

        :param file: The file to parse
        :param strategy: The parsing strategy to use
        :param kwargs: The parsing arguments
        :return: The job ID

        """

        # Retrieve the parser
        try:
            parser: Parser = self.parsers[strategy]
        except KeyError as ex:
            raise UnsupportedParser("Parser does not exist or is not enabled!") from ex
        except:
            logging.error(traceback.format_exc())
            raise

        # Create the job
        job: Job = await Job.create(
            parser=parser,
            file=file,
            criadex=self._criadex,
            redis=self._redis,
            **kwargs
        )

        # Store the job
        self._jobs[job.model.job_id] = job
        return job

    def get_job(self, job_id: str) -> Job:
        """
        Get a job by ID

        :param job_id: The job ID
        :raises JobNotFoundError: If the job is not found
        :return: The job

        """

        try:
            return self._jobs[job_id]
        except KeyError:
            raise JobNotFoundError(f"Job with ID {job_id} not found!") from None
