from typing import Optional, List, Any

from fastapi import APIRouter
from fastapi_utils.cbv import cbv
from starlette.requests import Request

from app.controllers.schemas import catch_exceptions, APIResponse, exception_response
from app.core.route import CriaRoute
from criaparse.job import JobModel, Job
from criaparse.models import Element
from criaparse.parsers.generic.errors import JobNotFoundError

view = APIRouter()


class ParserResultsResponse(APIResponse):
    job: Optional[JobModel] = None
    results: Optional[List[Element]] = None


@cbv(view)
class ParserResultsRoute(CriaRoute):
    ResponseModel = ParserResultsResponse

    @view.get(
        path="/parser/results",
        name="Get results for a file parse job",
        summary="Get results for a file parse job",
        description="Get results for a file parse job",
    )
    @catch_exceptions(
        ResponseModel
    )
    @exception_response(
        JobNotFoundError,
        ResponseModel(
            code="NOT_FOUND",
            status=404,
            message="The job with that ID was not found!",
        )
    )
    async def execute(
            self,
            request: Request,
            job_id: str
    ) -> ResponseModel:
        job: Job = request.app.criaparse.get_job(
            job_id=job_id
        )

        results: Optional[List[Any]] = None
        if await job.has_result():
            results = await job.get_result()

        # Success!
        return self.ResponseModel(
            code="SUCCESS",
            status=200,
            message="Successfully parsed the document.",
            job=job.model,
            results=results
        )


__all__ = ["view"]
