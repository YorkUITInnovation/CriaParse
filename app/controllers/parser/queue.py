from typing import Optional

from fastapi import APIRouter, UploadFile, File
from fastapi_utils.cbv import cbv
from starlette.requests import Request

from app.controllers.schemas import catch_exceptions, APIResponse, exception_response
from app.core.route import CriaRoute
from criaparse.client import ParseStrategy
from criaparse.job import JobModel, Job
from criaparse.parsers.generic.errors import ParseModelMissingError

view = APIRouter()


class ParserQueueResponse(APIResponse):
    job: Optional[JobModel] = None


@cbv(view)
class ParserParseRoute(CriaRoute):
    ResponseModel = ParserQueueResponse

    @view.post(
        path="/parser/queue",
        name="Queue a file parse job",
        summary="Queue a file parse job",
        description="Queue a file parse job",
    )
    @catch_exceptions(
        ResponseModel
    )
    @exception_response(
        ParseModelMissingError,
        ResponseModel(
            code="INVALID_PAYLOAD",
            status=400,
            message="You must provide valid LLM & Embedding models for this parsing strategy!",
        )
    )
    async def execute(
            self,
            request: Request,
            strategy: ParseStrategy,
            llm_model_id: Optional[int] = None,
            embedding_model_id: Optional[int] = None,
            file: UploadFile = File(...)
    ) -> ResponseModel:
        parse_response: Job = await request.app.criaparse.queue_parse(
            file=file,
            strategy=strategy,
            llm_model_id=llm_model_id,
            embedding_model_id=embedding_model_id
        )

        # Success!
        return self.ResponseModel(
            code="SUCCESS",
            status=200,
            message="Successfully queued the parse job.",
            job=parse_response.model
        )


__all__ = ["view"]
