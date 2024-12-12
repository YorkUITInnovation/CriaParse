import asyncio
import json
import time
import uuid
from typing import Dict, TYPE_CHECKING, Awaitable

from CriadexSDK import CriadexSDK
from CriadexSDK.routers.models.azure import ModelAboutRoute
from fastapi import UploadFile
from pydantic import BaseModel
from redis.asyncio import Redis

from criaparse.models import ParserResponse

if TYPE_CHECKING:
    from criaparse.parser import Parser


class JobModel(BaseModel):
    """
    A job to be processed by the job queue

    """

    job_id: str

    # Current step #
    step: int | None

    # Current step name
    step_name: str | None

    # Step count
    steps: int

    # Strategy name
    strategy: str

    # Timings Map<StepName, Time>
    step_timings: Dict[str, float] = {}


class Job:
    """
    A cria parsing job

    """

    def __init__(
            self,
            model: JobModel,
            parser: "Parser",
            redis_pool: Redis
    ):
        self._model: JobModel = model
        self._redis: Redis = redis_pool
        self._step_count = parser.step_count()
        self._parser: "Parser" = parser
        self._job_future: asyncio.Task | None = None
        self._expire_results_after = 60 * 60
        self._expire_time = time.time() + (60 * 60)
        self._redis_key = f"job:{self._model.job_id}"

    @property
    def expired(self) -> bool:
        """
        Check if the job has expired

        :return: True if the job has expired

        """

        return time.time() > self._expire_time

    def set_future(self, future: Awaitable | None) -> None:
        """
        Set the task for the job

        :param future: The task to set
        :return: The task

        """

        self._job_future = future

    @property
    def future(self) -> Awaitable:
        """
        Get the task for the job

        :return: The task

        """

        return self._job_future

    @property
    def model(self) -> JobModel:
        """
        Get the JSON model for the job status

        :return: The job model

        """

        return self._model

    @classmethod
    async def create(
            cls,
            parser: "Parser",
            file: UploadFile,
            criadex: CriadexSDK,
            redis: Redis,
            **kwargs
    ) -> "Job":
        """
        Create a job from a parser

        :param parser: The parser to use
        :param file: The file to parse
        :param criadex: The Criadex SDK
        :param redis: The Redis pool
        :param kwargs: kwargs
        :return: An instance of the Job class

        """

        # Create the job
        job: "Job" = cls(
            model=JobModel(
                job_id=str(uuid.uuid4()),
                step=None,
                steps=parser.step_count(),
                step_name=None,
                strategy=parser.parser_name()
            ),
            parser=parser,
            redis_pool=redis
        )

        # Get the result
        if kwargs['llm_model_id'] and kwargs['embedding_model_id']:
            llm_model_id = kwargs.pop('llm_model_id')
            embedding_model_id = kwargs.pop('embedding_model_id')

            # Get the model info from Criadex
            llm_model_info: ModelAboutRoute.Response = await criadex.models.azure.about(model_id=llm_model_id)
            embedding_model_info: ModelAboutRoute.Response = await criadex.models.azure.about(model_id=embedding_model_id)

            kwargs['llm_model_info'] = llm_model_info
            kwargs['embedding_model_info'] = embedding_model_info

        # Create the parse task
        job.set_future(job.execute_parser(
            file=file,
            job=job,
            **kwargs
        ))

        # Return them
        return job

    async def execute_parser(self, **kwargs) -> ParserResponse:
        """
        Handle the results of the job

        :param future: The future to handle

        """

        result: ParserResponse = await self._parser.parse(**kwargs)

        # Set the result
        await self.set_result(result)
        return result

    def set_step_finished(
            self,
            step_name: str,
            step_number: int,
            time_taken: float
    ) -> None:
        """
        Set a step as finished

        :param step_name: The name of the step
        :param step_number: The number of the step
        :param time_taken: The time taken for the step

        :return: The step finished

        """

        self._model.step_timings[step_name] = time_taken
        self._model.step = step_number
        self._model.step_name = step_name

    async def set_result(
            self,
            result: ParserResponse
    ) -> None:
        """
        Set the result of the job

        :param result: The result to set

        """

        await self._redis.set(
            self._redis_key,
            result.model_dump_json(),
            ex=self._expire_results_after
        )

    async def get_result(self) -> ParserResponse | None:
        """
        Get the result of the job

        :return: The result of the job

        """

        results = await self._redis.get(self._redis_key)

        if results is None:
            return None

        # Pop key once grabbed
        await self._redis.delete(self._redis_key)
        return ParserResponse(**json.loads(results))

    async def has_result(self) -> bool:
        """
        Check if the job has a result

        :return: Whether the job has a result

        """

        return await self._redis.exists(self._redis_key)
