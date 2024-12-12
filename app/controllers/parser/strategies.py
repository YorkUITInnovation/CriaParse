from typing import List

from fastapi import APIRouter
from fastapi_utils.cbv import cbv
from starlette.requests import Request

from app.controllers.schemas import catch_exceptions, APIResponse
from app.core.route import CriaRoute

view = APIRouter()


class ParserStrategiesResponse(APIResponse):
    strategies: List[str]


@cbv(view)
class ParserStrategiesRoute(CriaRoute):
    ResponseModel = ParserStrategiesResponse

    @view.get(
        path="/parser/strategies",
        name="List available parsing strategies",
        summary="List available parsing strategies",
        description="List available parsing strategies",
    )
    @catch_exceptions(
        ResponseModel
    )
    async def execute(
            self,
            request: Request,
    ) -> ResponseModel:
        # Success!
        return self.ResponseModel(
            code="SUCCESS",
            status=200,
            message="Successfully parsed the document.",
            strategies=request.app.criaparse.parsing_strategies
        )


__all__ = ["view"]
