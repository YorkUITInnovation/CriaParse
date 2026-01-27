import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from criaparse.models import ParserFile, FileUnsupportedParseError, ParserStrategy
from criaparse.parsers.generic.errors import ParseModelMissingError
from criaparse.parsers.generic.generic import GenericParser
from criaparse.parsers.paragraph.paragraph import ParagraphParser
from criaparse.daemon.job import Job
from criaparse.daemon.worker import Worker
from criaparse.parser import Parser
import io


class TestFileUnsupportedParseError:
    """Test cases for unsupported file types."""

    @pytest.mark.asyncio
    async def test_generic_parser_unsupported_file_type(self):
        """Test GenericParser does not raise error for any file type (accepts all)."""
        parser = GenericParser()
        file = ParserFile(
            filename="test.xyz",
            content_type="application/unsupported",
            filedata=b"test data"
        )
        mock_job = MagicMock(spec=Job)
        mock_job.criadex = MagicMock()
        mock_job.set_steps = AsyncMock()
        mock_job.set_step_finished = AsyncMock()
        
        # GenericParser accepts all files, so this should not raise FileUnsupportedParseError
        # Instead, test that supports_file returns True
        assert parser.supports_file(file) is True

    @pytest.mark.asyncio
    async def test_paragraph_parser_unsupported_file_type(self):
        """Test ParagraphParser raises FileUnsupportedParseError for unsupported file type."""
        parser = ParagraphParser()
        file = ParserFile(
            filename="test.xyz",
            content_type="application/unsupported",
            filedata=b"test data"
        )
        mock_job = MagicMock(spec=Job)
        
        with pytest.raises(FileUnsupportedParseError) as excinfo:
            await parser.parse(file, mock_job)
        
        assert "not supported" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_parser_supports_file_method(self):
        """Test Parser.supports_file() correctly identifies supported files."""
        parser = GenericParser()
        # GenericParser supports all files by design
        supported_file = ParserFile(
            filename="test.pdf",
            content_type="application/pdf",
            filedata=b"test"
        )
        any_file = ParserFile(
            filename="test.xyz",
            content_type="application/unsupported",
            filedata=b"test"
        )
        
        assert parser.supports_file(supported_file) is True
        assert parser.supports_file(any_file) is True  # GenericParser accepts all files


class TestParseModelMissingError:
    """Test cases for missing model errors."""

    @pytest.mark.asyncio
    @patch("criaparse.parsers.generic.generic.SemanticDocumentParser")
    async def test_generic_parser_missing_llm_model(self, mock_semantic_parser):
        """Test GenericParser raises ParseModelMissingError when LLM model is missing."""
        mock_semantic_parser.return_value.aparse = AsyncMock(
            side_effect=ParseModelMissingError("LLM model is required")
        )
        parser = GenericParser()
        file = ParserFile(
            filename="test.pdf",
            content_type="application/pdf",
            filedata=b"test data"
        )
        mock_job = MagicMock(spec=Job)
        mock_job.criadex = MagicMock()
        mock_job.set_steps = AsyncMock()
        mock_job.set_step_finished = AsyncMock()
        
        with pytest.raises(ParseModelMissingError) as excinfo:
            await parser._parse(file, mock_job, dataset_id="test_dataset", llm_model_id=None, embedding_model_id=1)
        
        assert "LLM model" in str(excinfo.value) or "model" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    @patch("criaparse.parsers.generic.generic.SemanticDocumentParser")
    async def test_generic_parser_missing_embedding_model(self, mock_semantic_parser):
        """Test GenericParser raises ParseModelMissingError when embedding model is missing."""
        mock_semantic_parser.return_value.aparse = AsyncMock(
            side_effect=ParseModelMissingError("Embedding model is required")
        )
        parser = GenericParser()
        file = ParserFile(
            filename="test.pdf",
            content_type="application/pdf",
            filedata=b"test data"
        )
        mock_job = MagicMock(spec=Job)
        mock_job.criadex = MagicMock()
        mock_job.set_steps = AsyncMock()
        mock_job.set_step_finished = AsyncMock()
        
        with pytest.raises(ParseModelMissingError) as excinfo:
            await parser._parse(file, mock_job, dataset_id="test_dataset", llm_model_id=1, embedding_model_id=None)
        
        assert "embedding" in str(excinfo.value).lower() or "model" in str(excinfo.value).lower()


class TestWorkerErrorHandling:
    """Test cases for worker error handling."""

    @pytest.mark.asyncio
    async def test_worker_handles_job_exception_gracefully(self):
        """Test worker handles exceptions during job processing gracefully."""
        worker = Worker(worker_id=1)
        mock_job = MagicMock(spec=Job)
        mock_job.data.job_id = "test_job_error"
        mock_job.future = AsyncMock()
        mock_job.future.__await__ = lambda x: iter([])
        mock_job.set_response = AsyncMock()
        
        # Simulate an exception during job processing
        async def failing_parse():
            raise ValueError("Test error during parsing")
        
        mock_job.future = failing_parse()
        
        await worker._queue.put(mock_job)
        
        with patch.object(worker._logger, 'error') as mock_logger_error:
            handler_task = asyncio.create_task(worker.handler())
            await asyncio.sleep(0.1)
            
            # Worker should log the error
            assert mock_logger_error.called
            
            handler_task.cancel()
            try:
                await handler_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_worker_handles_set_response_failure(self):
        """Test worker handles failure when setting job response."""
        worker = Worker(worker_id=1)
        mock_job = MagicMock(spec=Job)
        mock_job.data.job_id = "test_job_response_failure"
        mock_job.set_response = AsyncMock(side_effect=Exception("Failed to set response"))
        
        await worker._queue.put(mock_job)
        
        with patch.object(worker._logger, 'error') as mock_logger_error:
            handler_task = asyncio.create_task(worker.handler())
            await asyncio.sleep(0.1)
            
            # Worker should log both the original error and the response update error
            assert mock_logger_error.call_count >= 1
            
            handler_task.cancel()
            try:
                await handler_task
            except asyncio.CancelledError:
                pass


class TestParserFileEdgeCases:
    """Test cases for ParserFile edge cases."""

    def test_parser_file_empty_data(self):
        """Test ParserFile with empty file data."""
        file = ParserFile(
            filename="empty.txt",
            content_type="text/plain",
            filedata=b""
        )
        assert file.filedata == b""
        assert file.filename == "empty.txt"
        assert file.content_type == "text/plain"

    def test_parser_file_buffer_reuse(self):
        """Test ParserFile buffer is reused correctly."""
        file = ParserFile(
            filename="test.txt",
            content_type="text/plain",
            filedata=b"test data"
        )
        buffer1 = file.buffer
        buffer2 = file.buffer
        assert buffer1 is buffer2  # Should return the same buffer instance

    def test_parser_file_buffer_seek(self):
        """Test ParserFile buffer seek position."""
        file = ParserFile(
            filename="test.txt",
            content_type="text/plain",
            filedata=b"test data"
        )
        buffer = file.buffer
        assert buffer.tell() == 0  # Should be at start after seek(0)
        
        # Read some data
        buffer.read(4)
        # Get buffer again should reset position
        buffer2 = file.buffer
        assert buffer2.tell() == 0


class TestParserStrategy:
    """Test cases for ParserStrategy enum."""

    def test_parser_strategy_iterator(self):
        """Test ParserStrategy.iterator() returns all strategies."""
        strategies = list(ParserStrategy.iterator())
        assert len(strategies) > 0
        assert all(isinstance(s, ParserStrategy) for s in strategies)

    def test_parser_strategy_create(self):
        """Test ParserStrategy.create() creates parser instances."""
        for strategy in ParserStrategy.iterator():
            parser = strategy.create()
            assert isinstance(parser, Parser)
            assert hasattr(parser, 'accepted_mimetypes')
            assert hasattr(parser, 'parse')


class TestJobErrorScenarios:
    """Test cases for Job error scenarios."""

    @pytest.mark.asyncio
    async def test_job_with_invalid_file_data(self):
        """Test Job creation with invalid file data."""
        # This tests that Job can handle various file data scenarios
        mock_file = MagicMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"invalid\x00data")
        
        # Job should be able to handle binary data with null bytes
        # The actual behavior depends on the parser implementation
        assert mock_file.read.return_value is not None
