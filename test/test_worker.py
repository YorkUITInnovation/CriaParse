import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from criaparse.daemon.worker import Worker
from criaparse.daemon.job import Job
from criaparse.models import ParserResponse

@pytest.fixture
def worker_id():
    return 1

@pytest.fixture
def worker(worker_id):
    return Worker(worker_id=worker_id)

@pytest.mark.asyncio
async def test_worker_init(worker_id):
    worker = Worker(worker_id=worker_id)
    assert worker._worker_id == f"Ragflow-{worker_id}"
    assert worker._task is None
    assert worker._queue.empty()
    assert worker._logger is not None

@pytest.mark.asyncio
async def test_worker_queued(worker):
    assert worker.queued == 0
    await worker._queue.put(MagicMock(spec=Job))
    assert worker.queued == 1

@pytest.mark.asyncio
async def test_worker_start(worker):
    worker.start()
    assert worker._task is not None
    assert not worker._task.done() # Task should be running
    worker._task.cancel() # Clean up the task
    with pytest.raises(asyncio.CancelledError):
        await worker._task

@pytest.mark.asyncio
async def test_worker_stop(worker):
    worker.start()
    # Give the handler a chance to start and enter the loop
    await asyncio.sleep(0.01)
    await worker.stop()
    assert worker._task.done()
    # After graceful shutdown, the task should not raise CancelledError when awaited
    # Instead, it should complete normally.
    # We can assert that it's done and doesn't raise an exception.
    assert worker._task.exception() is None

@pytest.mark.asyncio
async def test_worker_queue(worker):
    mock_job = MagicMock(spec=Job)
    await worker.queue(mock_job)
    assert worker.queued == 1
    retrieved_job = await worker._queue.get()
    assert retrieved_job == mock_job

@pytest.mark.asyncio
async def test_worker_handler_success(worker):
    mock_job = MagicMock(spec=Job)
    mock_job.data.job_id = "test_job_id"
    # Create a mock future that can be awaited
    mock_future_result = MagicMock(spec=ParserResponse)
    mock_job.future = asyncio.Future()
    mock_job.future.set_result(mock_future_result)
    mock_job.set_response = AsyncMock()

    await worker._queue.put(mock_job)

    # Start the handler in a separate task
    handler_task = asyncio.create_task(worker.handler())

    # Wait for the job to be processed (give it some time)
    await asyncio.sleep(0.1)

    mock_job.set_response.assert_awaited_once_with(response=mock_future_result)

    handler_task.cancel()
    # After graceful shutdown, the task should not raise CancelledError when awaited
    # Instead, it should complete normally.
    await handler_task
    assert handler_task.done()
    assert handler_task.exception() is None

@pytest.mark.asyncio
async def test_worker_handler_cancelled(worker):
    # Put a dummy job to keep the handler running initially
    mock_job = MagicMock(spec=Job)
    mock_job.data.job_id = "dummy_job"
    mock_job.future = asyncio.Future()
    mock_job.future.set_exception(asyncio.CancelledError())
    await worker._queue.put(mock_job)

    handler_task = asyncio.create_task(worker.handler())

    # Cancel the handler task directly
    handler_task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await handler_task

@pytest.mark.asyncio
async def test_worker_handler_exception(worker):
    mock_job = MagicMock(spec=Job)
    mock_job.data.job_id = "test_job_id_exception"
    mock_job.future = asyncio.Future()
    mock_job.future.set_exception(Exception("Test Exception"))
    mock_job.set_response = AsyncMock()

    await worker._queue.put(mock_job)

    with patch.object(worker._logger, 'error') as mock_logger_error:
        handler_task = asyncio.create_task(worker.handler())
        await asyncio.sleep(0.1) # Give time for exception to be handled

        mock_logger_error.assert_called_once()
        # Check if the exception message is present in the exc_info part of the log
        assert mock_logger_error.call_args[1]['exc_info'] is not None
        assert "Test Exception" in str(mock_logger_error.call_args[1]['exc_info'])

        handler_task.cancel()
        # After graceful shutdown, the task should not raise CancelledError when awaited
        # Instead, it should complete normally.
        # We can assert that it's done and doesn't raise an exception.
        await handler_task
        assert handler_task.done()
        assert handler_task.exception() is None
