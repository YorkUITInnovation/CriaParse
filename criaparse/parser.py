import io
from abc import ABC, abstractmethod
from io import BytesIO
from typing import List, BinaryIO, Awaitable

from CriadexSDK.routers.models.azure import ModelAboutRoute
from fastapi import UploadFile

from criaparse.job import Job
from criaparse.models import ParserResponse


class FileUnsupportedParseError(RuntimeError):
    """
    Thrown when someone tries to parse a file not supported by a parser

    """


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

    def to_buffer(self, file: UploadFile) -> io.BytesIO:
        file: BinaryIO = file.file
        file.seek(0)
        io: BytesIO = BytesIO()
        io.write(file.read())

        return io

    async def parse(
            self,
            file: UploadFile,
            job: Job,
            **kwargs
    ) -> ParserResponse:
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
    def parser_name(cls) -> str:
        """
        Get the name of the parser

        :return: The parser name

        """

        raise NotImplementedError
