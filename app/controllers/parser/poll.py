import uuid
from typing import Optional

from fastapi import APIRouter
from fastapi_utils.cbv import cbv
from starlette.requests import Request

from app.controllers.schemas import catch_exceptions, APIResponse
from app.core.route import CriaRoute
from criaparse.daemon.job import JobData

view = APIRouter()


class ParserPollResponse(APIResponse):
    job: Optional[JobData] = None


@cbv(view)
class ParserPollRoute(CriaRoute):
    ResponseModel = ParserPollResponse
    Description = "Poll the results of a file parse job."

    @view.get(
        path="/parser/poll",
        name=Description,
        summary=Description,
        description=Description
    )
    @catch_exceptions(
        ResponseModel
    )
    async def execute(
            self,
            request: Request,
            job_id: uuid.UUID
    ) -> ResponseModel:
        job_data: JobData | None = await request.app.criaparse.poll(job_id=job_id)

        # If no job is found
        if job_data is None:
            return self.ResponseModel(
                code="NOT_FOUND",
                status=404,
                message=f"The job with the ID {job_id} was not found!",
            )

        # Success!
        return self.ResponseModel(
            code="SUCCESS",
            status=200,
            message="Successfully parsed the document.",
            job=job_data
        )


__all__ = ["view"]
