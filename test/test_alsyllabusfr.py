import pytest
from unittest.mock import AsyncMock, patch, Mock
from criaparse.models import ParserFile, ParserResponse, Element, ElementType, ParserStrategy
from criaparse.daemon.job import Job
from criaparse.parsers.alsyllabusfr.alsyllabusfr import AlSyllabusParserFr

@pytest.mark.asyncio
async def test_alsyllabus_parser_fr_parse():
    parser = AlSyllabusParserFr()

    # Mock the ParserFile
    mock_file = AsyncMock(spec=ParserFile)
    mock_file.buffer = b"mock file content"

    # Mock the Job object
    mock_job = AsyncMock(spec=Job)

    # Mock the run_converter function
    mock_parsed_elements = [
        Element(type=ElementType.TITLE, text="Mock Title Fr", metadata={}),
        Element(type=ElementType.NARRATIVE_TEXT, text="Mock Text Fr", metadata={}),
    ]

    with patch('criaparse.parsers.alsyllabusfr.alsyllabusfr.run_converter', return_value=mock_parsed_elements) as mock_run_converter:
        response: ParserResponse = await parser._parse(mock_file, mock_job)

        mock_run_converter.assert_called_once_with(docx=mock_file.buffer)
        mock_job.set_step_finished.assert_called_once()

        assert isinstance(response, ParserResponse)
        assert len(response.elements) == 2

        assert response.elements[0].type == ElementType.TITLE
        assert response.elements[0].text == "Mock Title Fr"

        assert response.elements[1].type == ElementType.NARRATIVE_TEXT
        assert response.elements[1].text == "Mock Text Fr"

def test_alsyllabus_parser_fr_strategy():
    assert AlSyllabusParserFr.strategy() == ParserStrategy.AL_SYLLABUS_FR

def test_alsyllabus_parser_fr_accepted_mimetypes():
    parser = AlSyllabusParserFr()
    expected_mimetypes = ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    assert parser.accepted_mimetypes() == expected_mimetypes
