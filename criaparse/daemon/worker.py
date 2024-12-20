import asyncio
import logging
from asyncio import Queue

from criaparse.daemon.job import Job
from criaparse.models import ParserResponse


class Worker:
    """A simple worker to handle CriaParse jobs"""

    def __init__(
            self,
            worker_id: int
    ):
        self._worker_id: str = f"Llama-{worker_id}"
        self._task: asyncio.Task | None = None
        self._queue: Queue[Job] = Queue()
        self._logger: logging.Logger = logging.getLogger('uvicorn.info')
        self._logger_prefix: str = f"[CriaParse] "

    @property
    def queued(self) -> int:
        """Check the # of queued tasks"""
        return self._queue.qsize()

    def start(self) -> None:
        """Start the worker"""
        self._logger.info(self._logger_prefix + f"Worker {self._worker_id} is now starting...")
        self._task = asyncio.create_task(self.handler())

    async def stop(self) -> None:
        """Stop the worker"""
        self._task.cancel()
        await self._task

    async def queue(self, job: Job) -> None:
        """Add a job to the worker queue"""
        await self._queue.put(job)

    async def handler(self) -> None:
        """Handle items in the worker queue"""
        current_job_id: str | None = None

        while True:
            # Parse jobs
            try:
                current_job_id = None
                # Wait until a job has been added
                job: Job = await self._queue.get()
                current_job_id = job.data.job_id
                self._logger.info(self._logger_prefix + f"Worker {self._worker_id} is now processing job \"{current_job_id}\"")

                # Complete the job
                job_result: ParserResponse = await job.future

                # Set the parser response
                await job.set_response(response=job_result)
                self._logger.info(self._logger_prefix + f"Worker {self._worker_id} has completed job \"{current_job_id}\"")

            # Gracefully shut down
            except asyncio.CancelledError:
                self._logger.info(self._logger_prefix + f"Worker {self._worker_id} is shutting down with {self.queued} queued jobs...")
                break

            # Ignore exceptions & log
            except Exception:
                self._logger.error(self._logger_prefix + f"Worker {self._worker_id} encountered an error while processing job \"{current_job_id}\".", exc_info=True)
                continue
