from pathlib import Path

from fastapi import APIRouter
from fastapi_utils.cbv import cbv
from starlette.responses import Response

from app.controllers.schemas import catch_exceptions, APIResponse
from app.core import config
from app.core.route import CriaRoute
from app.core.schemas import AppMode

view = APIRouter()


@cbv(view)
class DocsStylesRoute(CriaRoute):
    ResponseModel = Response
    CSS_FP: Path = Path(__file__).parent.joinpath("theme.css")
    CSS: str = open(CSS_FP, "r").read()
    Description = "Get the CSS for the theme"

    def get_css(self) -> str:
        """Get CSS for theme"""

        if config.APP_MODE == AppMode.PRODUCTION:
            return self.CSS
        return open(self.CSS_FP, "r").read()

    @view.get(
        "/styles",
    )
    @catch_exceptions(
        APIResponse
    )
    async def execute(self) -> ResponseModel:
        return Response(
            content=self.get_css(),
            headers={"Content-Type": "text/css"}
        )


__all__ = ["view"]
