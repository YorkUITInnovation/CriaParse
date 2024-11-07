import logging
import traceback
from typing import Dict, List, Type, Literal

from CriadexSDK import CriadexSDK
from fastapi import UploadFile

from criaparse.parser import Parser, Element
from criaparse.parsers.alsyllabus.alsyllabus import AlSyllabusParser
from criaparse.parsers.alsyllabusfr.alsyllabusfr import AlSyllabusParserFr
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

    def __init__(self, criadex: CriadexSDK):
        """
        Initialize the enabled parsers

        """

        self._criadex: CriadexSDK = criadex

        self.parsers: Dict[ParseStrategy, Parser] = {
            "GENERIC": GenericParser(),
            "ALSYLLABUS": AlSyllabusParser(),
            "ALSYLLABUSFR": AlSyllabusParserFr(),
            "PARAGRAPH": ParagraphParser()
        }

    @property
    def parsing_strategies(self) -> List[str]:
        return list(self.parsers.keys())

    async def parse(
            self,
            file: UploadFile,
            strategy: ParseStrategy = "GENERIC",
            **kwargs
    ) -> List[Element]:
        """
        Parse a document using the CriaParse suite

        :param file: The file to parse
        :param strategy: The parsing strategy to use
        :return: The parsed file

        """

        # Retrieve the parser
        try:
            parser: Parser = self.parsers[strategy]
        except KeyError as ex:
            raise UnsupportedParser("Parser does not exist or is not enabled!") from ex
        except:
            logging.error(traceback.format_exc())
            raise

        # Parse the file
        return await parser.parse(file=file, criadex=self._criadex, **kwargs)
