from typing import Optional, List

from fastapi import APIRouter, UploadFile, File
from fastapi_utils.cbv import cbv
from starlette.requests import Request

from app.controllers.schemas import catch_exceptions, APIResponse, exception_response
from app.core.route import CriaRoute
from criaparse.models import Element, ParserResponse, Asset, ParserStrategy
from criaparse.parsers.generic.errors import ParseModelMissingError

view = APIRouter()


class ParserParseResponse(APIResponse):
    nodes: Optional[List[Element]] = None
    assets: Optional[List[Asset]] = None


@cbv(view)
class ParserParseRoute(CriaRoute):
    ResponseModel = ParserParseResponse
    Description = "Parse a file synchronously & get the result. Subject to timeout errors for large files."

    @view.post(
        path="/parser/parse",
        name="Parse a file",
        summary="Parse a file",
        description="Parse a file",
        deprecated=True
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
            strategy: ParserStrategy,
            llm_model_id: Optional[int] = None,
            embedding_model_id: Optional[int] = None,
            file: UploadFile = File(...)
    ) -> ResponseModel:
        # Get the job response
        job_response: ParserResponse = await request.app.criaparse.parse_sync(
            file=file,
            strategy=strategy,
            llm_model_id=llm_model_id,
            embedding_model_id=embedding_model_id
        )

        # Success!
        return self.ResponseModel(
            code="SUCCESS",
            status=200,
            message="Successfully parsed the document.",
            nodes=job_response.elements,
            assets=job_response.assets
        )


__all__ = ["view"]
