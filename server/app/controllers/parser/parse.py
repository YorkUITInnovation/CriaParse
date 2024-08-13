from typing import Optional, List

from fastapi import APIRouter, UploadFile, File
from fastapi_restful.cbv import cbv
from starlette.requests import Request

from app.controllers.schemas import catch_exceptions, APIResponse, exception_response
from app.core.route import CriaRoute
from criaparse.client import ParseStrategy
from criaparse.parser import Element
from criaparse.parsers.generic.errors import ParseModelMissingError

view = APIRouter()


class ParserParseResponse(APIResponse):
    nodes: Optional[List[Element]] = None


@cbv(view)
class ParserParseRoute(CriaRoute):
    ResponseModel = ParserParseResponse

    @view.post(
        path="/parser/parse",
        name="Parse a file",
        summary="Parse a file",
        description="Parse a file",
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

        parse_response: List[Element] = await request.app.criaparse.parse(
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
            nodes=parse_response
        )


__all__ = ["view"]
