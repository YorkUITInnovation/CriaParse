from criaparse.daemon.job import Job
from criaparse.daemon.worker import Worker


class Daemon:
    """Handles the management of asynchronous parsing jobs"""

    def __init__(
            self,
            workers: int
    ):
        # Create workers
        self._workers: list[Worker] = [Worker(worker_id=idx + 1) for idx in range(workers)]

    def start(self) -> None:
        """Start the daemon"""
        for worker in self._workers:
            worker.start()

    async def stop(self) -> None:
        """Stop the daemon"""
        for worker in self._workers:
            await worker.stop()

    async def queue(self, job: Job) -> Job:
        """Add to the worker with the least amount of jobs queued"""

        # Find the worker with the least amount of jobs
        worker = min(self._workers, key=lambda w: w.queued)
        await worker.queue(job=job)
        return job
