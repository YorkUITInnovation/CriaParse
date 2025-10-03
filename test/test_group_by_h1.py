
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from criaparse.parsers.generic.generic import GenericParser
from criaparse.models import ParserFile
from criaparse.daemon.job import Job
from ragflow_sdk import RAGFlow
import io


@pytest.fixture
def mock_ragflow_client():
    """Fixture for a mocked RAGFlow client."""
    mock_client = MagicMock(autospec=RAGFlow)
    mock_client.upload_file.return_value = {"doc_ids": ["test_doc_id"]}
    mock_client.get_chunks.return_value = [
        {"type": "text", "content": "This is a text chunk."},
        {"type": "image", "content": "This is an image caption."},
        {"type": "table", "content": "This is a table chunk."},
    ]
    return mock_client


@pytest.fixture
def mock_job(mock_ragflow_client):
    """Fixture for a mocked Job."""
    mock_job = MagicMock(autospec=Job)
    mock_job.criadex.ragflow = mock_ragflow_client
    mock_job.set_steps = AsyncMock()
    mock_job.set_step_finished = AsyncMock()
    return mock_job


@pytest.mark.asyncio
@patch("criaparse.parsers.generic.generic.GenericParser.group_elements_and_extract_assets", return_value=([], []))
@patch("criaparse.parsers.generic.generic.SemanticDocumentParser")
async def test_group_by_h1_disabled(mock_semantic_parser, mock_group_elements, mock_job):
    """Test the group_by_h1 feature."""
    mock_semantic_parser.return_value.aparse = AsyncMock(return_value=([{"type": "text", "text": "test", "metadata": {}}], {}))
    parser = GenericParser()
    file_content = b"This is a test document."
    file = ParserFile(
        filename="test.txt",
        content_type="text/plain",
        filedata=file_content,
    )
    kwargs = {"dataset_id": "test_dataset", "group_by_h1": False}

    result = await parser._parse(file, mock_job, **kwargs)

    assert result is not None
    mock_group_elements.assert_not_called()
