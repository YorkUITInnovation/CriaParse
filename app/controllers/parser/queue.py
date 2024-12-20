from typing import Optional

from fastapi import APIRouter, UploadFile, File
from fastapi_utils.cbv import cbv
from starlette.requests import Request

from app.controllers.schemas import catch_exceptions, APIResponse, exception_response
from app.core.route import CriaRoute
from criaparse.daemon.job import Job, JobData
from criaparse.models import ParserStrategy, FileUnsupportedParseError
from criaparse.parsers.generic.errors import ParseModelMissingError

view = APIRouter()


class ParserQueueResponse(APIResponse):
    job: Optional[JobData] = None


@cbv(view)
class ParserParseRoute(CriaRoute):
    ResponseModel = ParserQueueResponse
    Description = "Queue a file parse job"

    @view.post(
        path="/parser/queue",
        name=Description,
        summary=Description,
        description=Description,
    )
    @catch_exceptions(
        ResponseModel
    )
    @exception_response(
        ParseModelMissingError,
        ResponseModel(
            code="INVALID_PAYLOAD",
            status=400,
            message="You must provide valid LLM & embedding models for this parsing strategy!",
        )
    )
    async def execute(
            self,
            request: Request,
            strategy: ParserStrategy,
            llm_model_id: Optional[int] = None,
            embedding_model_id: Optional[int] = None,
            al_extension: Optional[bool] = False,
            file: UploadFile = File(...),
    ) -> ResponseModel:

        try:
            # Queue a Job
            job: Job = await request.app.criaparse.queue(
                file=file,
                strategy=strategy,
                llm_model_id=llm_model_id,
                embedding_model_id=embedding_model_id,
                al_extension=al_extension
            )
        except FileUnsupportedParseError as ex:
            return self.ResponseModel(
                code="INVALID_PAYLOAD",
                status=400,
                message=str(ex)
            )

        # Return the response
        return self.ResponseModel(
            code="SUCCESS",
            status=200,
            message="Successfully queued the parse job.",
            job=job.data
        )


__all__ = ["view"]
