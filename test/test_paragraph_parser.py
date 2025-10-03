import pytest
from unittest.mock import AsyncMock, patch, Mock
from criaparse.models import ParserFile, ParserResponse, Element, ElementType, ParserStrategy
from criaparse.parsers.paragraph.paragraph import ParagraphParser

@pytest.mark.asyncio
async def test_paragraph_parser_parse():
    parser = ParagraphParser()

    # Mock the ParserFile
    mock_file = AsyncMock(spec=ParserFile)
    mock_file.buffer = b"mock file content"

    # Mock the run_converter function
    mock_parsed_elements = [
        Element(type=ElementType.NARRATIVE_TEXT, text="Mock Paragraph 1", metadata={}),
        Element(type=ElementType.NARRATIVE_TEXT, text="Mock Paragraph 2", metadata={}),
    ]

    with patch('criaparse.parsers.paragraph.paragraph.run_converter', return_value=mock_parsed_elements) as mock_run_converter:
        response: ParserResponse = await parser._parse(mock_file)

        mock_run_converter.assert_called_once_with(docx=mock_file.buffer)

        assert isinstance(response, ParserResponse)
        assert len(response.elements) == 2

        assert response.elements[0].type == ElementType.NARRATIVE_TEXT
        assert response.elements[0].text == "Mock Paragraph 1"

        assert response.elements[1].type == ElementType.NARRATIVE_TEXT
        assert response.elements[1].text == "Mock Paragraph 2"

def test_paragraph_parser_strategy():
    assert ParagraphParser.strategy() == ParserStrategy.PARAGRAPH

def test_paragraph_parser_accepted_mimetypes():
    parser = ParagraphParser()
    expected_mimetypes = ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    assert parser.accepted_mimetypes() == expected_mimetypes
