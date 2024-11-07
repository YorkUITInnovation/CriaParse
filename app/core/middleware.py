import json

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class StatusMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):

        response: Response = await call_next(request)

        if response.headers.get('content-type') == 'application/json':
            return await self.handle_json_status(response)

        return response

    async def handle_json_status(self, response: Response):
        binary = b''

        # noinspection PyUnresolvedReferences
        async for data in response.body_iterator:
            binary += data

        body: dict = json.loads(binary.decode())

        if "error" in body and not body["error"]:
            del body["error"]

        return JSONResponse(
            content=body,
            status_code=body.get('status', response.status_code)
        )
