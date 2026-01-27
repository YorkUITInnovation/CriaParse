from fastapi import APIRouter, Request
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
    async def execute(self, request: Request) -> ResponseModel:
        # Preserve API key in redirect if provided
        api_key = request.query_params.get("x-api-key") or request.headers.get("x-api-key")
        redirect_url = "/docs"
        if api_key:
            redirect_url = f"/docs?x-api-key={api_key}"
        return self.ResponseModel(url=redirect_url)


__all__ = ["view"]
