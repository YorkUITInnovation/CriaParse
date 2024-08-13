import logging

from fastapi import APIRouter
from starlette.responses import Response

from app.controllers import docs, parser

router = APIRouter()

router.include_router(docs.router)
router.include_router(parser.router)


class HealthCheckFilter(logging.Filter):
    HEALTH_ENDPOINT: str = "/health_check"

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(self.HEALTH_ENDPOINT) == -1


logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


@router.get(HealthCheckFilter.HEALTH_ENDPOINT, include_in_schema=False)
async def health_check() -> Response:
    """
    Check if the server is online (for docker health check)
    :return: Just a simple 200

    """

    return Response(status_code=200, content="Pong!")


__all__ = ["router"]
