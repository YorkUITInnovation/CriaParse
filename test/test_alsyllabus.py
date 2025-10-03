import pytest
from unittest.mock import AsyncMock, patch
from criaparse.models import ParserFile, ParserResponse, Element, ElementType, ParserStrategy
from criaparse.parsers.alsyllabus.alsyllabus import AlSyllabusParser
from criaparse.parsers.alsyllabus.al_types import AlNode

@pytest.mark.asyncio
async def test_alsyllabus_parser_parse():
    parser = AlSyllabusParser()

    # Mock the ParserFile
    mock_file = AsyncMock(spec=ParserFile)
    mock_file.buffer = b"mock file content"

    # Mock the convert_file function
    mock_al_nodes: list[AlNode] = [
        {"type": "Title", "text": "Mock Title", "metadata": {"page_number": 1}},
        {"type": "NarrativeText", "text": "Mock Text", "metadata": {"page_number": 1}},
    ]

    with patch('criaparse.parsers.alsyllabus.alsyllabus.convert_file', return_value=mock_al_nodes) as mock_convert_file:
        response: ParserResponse = await parser._parse(mock_file)

        mock_convert_file.assert_called_once_with(file_bytes=mock_file.buffer)

        assert isinstance(response, ParserResponse)
        assert len(response.elements) == 2

        assert response.elements[0].type == ElementType.TITLE
        assert response.elements[0].text == "Mock Title"
        assert response.elements[0].metadata == {"page_number": 1}

        assert response.elements[1].type == ElementType.NARRATIVE_TEXT
        assert response.elements[1].text == "Mock Text"
        assert response.elements[1].metadata == {"page_number": 1}

def test_alsyllabus_parser_strategy():
    assert AlSyllabusParser.strategy() == ParserStrategy.AL_SYLLABUS

def test_alsyllabus_parser_accepted_mimetypes():
    parser = AlSyllabusParser()
    expected_mimetypes = ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    assert parser.accepted_mimetypes() == expected_mimetypes
