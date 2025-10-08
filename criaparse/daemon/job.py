from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import TYPE_CHECKING, Awaitable, Dict

from CriadexSDK.ragflow_sdk import RAGFlowSDK as CriadexSDK
from fastapi import UploadFile
from pydantic import BaseModel, PrivateAttr, Field
from redis import Redis
from redis.asyncio import Redis

from criaparse.models import ParserResponse, ParserFile

if TYPE_CHECKING:
    from criaparse.parser import Parser


class Job:
    """A parsing job to be processed by the job queue"""

    def __init__(
            self,
            job_data: JobData,
    ):
        """Create a Job instance"""

        # The future
        self._future: asyncio.Task | None = None

        # The Redis data model
        self._data: JobData = job_data

    @classmethod
    async def create(
            cls,
            parser: "Parser",
            file: UploadFile,
            criadex: CriadexSDK,
            redis: Redis,
            **kwargs
    ) -> Job:
        """
        Create a job from a parser

        :param parser: The parser to use
        :param file: The file to parse
        :param criadex: The Criadex SDK
        :param redis: The Redis pool
        :param kwargs: kwargs
        :return: An instance of the Job class

        """

        job_data: JobData = JobData(
            # Public attrs
            step=None,
            steps=parser.step_count(**kwargs),  # Number of steps may depend on kwarg config
            step_name=None,
            strategy=parser.name(),

            # Private attrs
            _redis=redis
        )

        # Create Job
        job: "Job" = cls(job_data=job_data)

        # Get the model information dynamically
        if kwargs['llm_model_id'] and kwargs['embedding_model_id']:
            llm_model_id = kwargs.pop('llm_model_id')
            embedding_model_id = kwargs.pop('embedding_model_id')

            # Get the model info from Criadex
            llm_model_info = await criadex.models.about(model_id=llm_model_id)
            embedding_model_info = await criadex.models.about(model_id=embedding_model_id)

            kwargs['llm_model_info'] = llm_model_info
            kwargs['embedding_model_info'] = embedding_model_info

        # Convert the file here to prevent io stream closing by FastAPI
        parser_file = await ParserFile.from_upload_file(upload_file=file)

        # Start the job & return the Job instance
        return await job.start(
            parser.parse(
                file=parser_file,
                job=job,
                **kwargs
            )
        )

    @property
    def future(self) -> Awaitable[ParserResponse] | None:
        """The future representing the Job completion """
        return self._future

    async def start(self, future: Awaitable[ParserResponse]) -> Job:
        """Set the future for the job"""
        self._future = future
        await self._data.upsert()
        return self

    @property
    def data(self) -> JobData:
        """Redis model for the ob"""
        return self._data

    async def set_steps(
            self,
            steps: dict[int, str]
    ):

        # Initialize the timings for the steps
        for step_num, step_name in steps.items():
            self._data.step_timings[step_num] = JobDataTiming(
                step_name=step_name,
                time_taken=None,
                timestamp_completed=None
            )

        await self._data.upsert()

    async def set_step_finished(
            self,
            step_name: str,
            step_number: int,
            time_taken: float
    ) -> None:
        """
        Set a step in the parsing job as finished

        :param step_name: The name of the step
        :param step_number: The number of the step
        :param time_taken: The time taken for the step

        """

        # Update the pertinent data
        self._data.step_timings[step_number] = JobDataTiming(
            step_name=step_name,
            time_taken=time_taken,
            timestamp_completed=round(time.time() * 1000)
        )

        self._data.step = step_number
        self._data.step_name = step_name

        # Update the JobData model
        await self._data.upsert()

    async def set_response(
            self,
            response: ParserResponse
    ) -> None:
        """
        Set the result of the job

        """

        # Update the new data
        self._data.finished = True
        self._data.response = response

        await self._data.upsert()


class JobDataTiming(BaseModel):
    """
    Timing data for a job

    """

    step_name: str
    time_taken: float | None
    timestamp_completed: float | None


class JobData(BaseModel):
    """
    A job to be processed by the job queue

    """

    # Private redis for sync'ing the model
    _redis: Redis = PrivateAttr()

    # The ID of the job
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Current step #
    step: int | None

    # Current step name
    step_name: str | None

    # Step count
    steps: int

    # Strategy name
    strategy: str

    # Timings Map<StepName, Time>
    step_timings: Dict[int, JobDataTiming] = {}

    # Response
    response: ParserResponse | None = None

    # Whether finished
    finished: bool = False

    def __init__(self, _redis: Redis, **kwargs):
        """Create a JobData instance"""
        super().__init__(**kwargs)
        self._redis = _redis

    async def upsert(self) -> None:
        """Upsert the job data. Expires after 1 hour."""
        await self._redis.set(self._create_key(self.job_id), self.json(), ex=(60 * 60))

    async def delete(self) -> None:
        """Delete the job data from redis"""
        await self._redis.delete(self._create_key(job_id=self.job_id))

    @classmethod
    async def from_redis(cls, job_id: str, redis: Redis) -> JobData | None:
        """Load the job data from Redis"""
        data: str | None = await redis.get(cls._create_key(job_id=job_id))
        return cls(**json.loads(data), _redis=redis) if data is not None else None

    @classmethod
    def _create_key(cls, job_id: str) -> str:
        """Get the redis Key for a job"""
        return f"criaparse:job:{job_id}"
