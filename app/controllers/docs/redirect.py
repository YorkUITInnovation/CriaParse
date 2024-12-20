from fastapi import APIRouter
from fastapi_utils.cbv import cbv
from starlette.responses import RedirectResponse

from app.controllers.schemas import catch_exceptions, APIResponse
from app.core.route import CriaRoute

view = APIRouter()


@cbv(view)
class DocsRedirectRoute(CriaRoute):
    ResponseModel = RedirectResponse
    Description = "Redirect to the Swagger UI documentation."

    @view.get(
        "/",
        name=Description,
    )
    @catch_exceptions(
        APIResponse
    )
    async def execute(self) -> ResponseModel:
        return self.ResponseModel(
            url="/docs"
        )


__all__ = ["view"]
