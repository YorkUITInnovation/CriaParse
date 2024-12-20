import io
from abc import ABC, abstractmethod
from io import BytesIO
from typing import List, BinaryIO

from fastapi import UploadFile

from criaparse.daemon.job import Job
from criaparse.models import ParserResponse, FileUnsupportedParseError


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
    async def _parse(self, file: UploadFile, job: "Job", **kwargs) -> ParserResponse:
        """
        Parse a document with the parser

        :return: The parsed element list

        """

        raise NotImplementedError

    @classmethod
    def to_buffer(cls, file: UploadFile) -> io.BytesIO:
        """Convert an UploadFile to a BytesIO buffer"""

        file: BinaryIO = file.file
        file.seek(0)
        buffer: BytesIO = BytesIO()
        buffer.write(file.read())

        return buffer

    async def parse(
            self,
            file: UploadFile,
            job: Job,
            **kwargs
    ) -> "ParserResponse":
        """
        Parse a document with the parser

        :return: The parsed element list

        """

        if not self.supports_file(file=file):
            raise FileUnsupportedParseError(
                f"The file content type {file.content_type} is not supported by {type(self)}"
            )

        return await self._parse(file=file, job=job, **kwargs)

    @classmethod
    @abstractmethod
    def step_count(cls) -> int:
        """
        Get the number of steps in the parser

        :return: The number of steps

        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """
        Get the name of the parser

        :return: The parser name

        """

        raise NotImplementedError
