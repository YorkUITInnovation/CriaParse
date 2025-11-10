
import pytest
from unittest.mock import MagicMock, AsyncMock
from criaparse.parsers.generic.generic import RAGFlowWrapper
from ragflow_sdk import RAGFlow
import os
import tempfile

@pytest.fixture
def mock_criadex_sdk():
    """Fixture for a mocked Criadex SDK."""
    mock_sdk = MagicMock()
    mock_sdk.content.upload = AsyncMock(return_value={"document_name": "test_doc_id"})
    return mock_sdk

@pytest.mark.asyncio
async def test_ragflow_wrapper_get_chunks(mock_criadex_sdk):
    """
    Test that RAGFlowWrapper.get_chunks correctly chunks content using unstructured.
    """
    wrapper = RAGFlowWrapper(criadex_sdk=mock_criadex_sdk, dataset_id="test_dataset")
    
    # Simulate uploading a file
    test_content = (
        "This is the first sentence of a paragraph. "
        "This is the second sentence. "
        "This is the third sentence. "
        "This is a new paragraph. "
        "It has two sentences."
    )
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name
    
    try:
        await wrapper.upload_file("test_dataset", temp_file_path)
        
        # Now call get_chunks
        chunks = wrapper.get_chunks("test_doc_id") # doc_id is not used by get_chunks in RAGFlowWrapper
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        
        # Verify content of chunks (simple check for now)
        # unstructured.chunk_by_title with default params will likely create one chunk for this short text
        assert len(chunks) == 1
        assert "content" in chunks[0]
        assert chunks[0]["content"] == test_content
        
        # Test with content that should be split
        long_content = "A" * 1500 + ". " + "B" * 1500 + "."
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp_file_long:
            temp_file_long.write(long_content)
            temp_file_path_long = temp_file_long.name
        
        await wrapper.upload_file("test_dataset", temp_file_path_long)
        chunks_long = wrapper.get_chunks("test_doc_id_long")
        
        assert len(chunks_long) > 1 # Should be split into multiple chunks
        assert "content" in chunks_long[0]
        assert "content" in chunks_long[1]

    finally:
        os.remove(temp_file_path)
        if 'temp_file_path_long' in locals() and os.path.exists(temp_file_path_long):
            os.remove(temp_file_path_long)
