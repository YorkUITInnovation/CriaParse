from typing import List

from CriadexSDK import CriadexSDK
from fastapi import UploadFile
from redis.asyncio import Redis

from criaparse.daemon.daemon import Daemon
from criaparse.daemon.job import Job, JobData
from criaparse.models import ParserResponse, ParserStrategy


class CriaParse:
    """Manager for handling parsing jobs"""

    def __init__(
            self,
            criadex: CriadexSDK,
            redis: Redis,
            workers: int
    ):
        """Initialize CriaParse"""

        self._criadex: CriadexSDK = criadex
        self._parsers = {strategy: strategy.create() for strategy in ParserStrategy.iterator()}
        self._redis: Redis = redis
        self._daemon = Daemon(workers=workers)

    def start(self) -> None:
        """Start the Daemon responsible for handling asynchronous parsing jobs."""
        self._daemon.start()

    async def close(self):
        """Stop the Daemon responsible for handling asynchronous parsing jobs & cancel all jobs."""
        await self._daemon.stop()

    @property
    def parsing_strategies(self) -> List[str]:
        """List the available parser strategies"""
        return list(self._parsers.keys())

    async def parse_sync(
            self,
            file: UploadFile,
            strategy: ParserStrategy,
            **kwargs
    ) -> ParserResponse:
        """(NOT RECOMMENDED) Synchronously parse a file using a specific strategy. This will lead to HTTP timeouts on large documents when hooked into FastAPI."""

        job: Job = await Job.create(
            parser=self._parsers[strategy],
            criadex=self._criadex,
            redis=self._redis,
            file=file,
            **kwargs
        )

        # Wait for response without using a worker
        return await job.future

    async def queue(
            self,
            file: UploadFile,
            strategy: ParserStrategy,
            **kwargs
    ) -> Job:
        """Queue a job to be processed by the daemon"""

        # Default to H1-grouped nodes for indexing when using the GENERIC strategy
        if strategy == ParserStrategy.GENERIC and 'group_by_h1' not in kwargs:
            kwargs['group_by_h1'] = True

        job: Job = await Job.create(
            parser=self._parsers[strategy],
            criadex=self._criadex,
            redis=self._redis,
            file=file,
            **kwargs
        )

        return await self._daemon.queue(job=job)

    async def poll(self, job_id: str) -> JobData | None:
        """Poll the status of a job"""

        # Get the key
        job_data: JobData | None = await JobData.from_redis(job_id=job_id, redis=self._redis)

        # If no response
        if job_data is None:
            return None

        # If it's finished, delete the key as we are retrieving the parse data
        if job_data.finished:
            await job_data.delete()

        # Return the data
        return job_data
