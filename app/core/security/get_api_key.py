import logging
from abc import abstractmethod
from typing import Optional

from CriadexSDK import CriadexSDK
from CriadexSDK.routers.auth import AuthCheckRoute
from CriadexSDK.routers.group_auth import GroupAuthCheckRoute
from fastapi import Security, HTTPException
from fastapi.security import APIKeyQuery, APIKeyHeader
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.controllers.schemas import UnauthorizedResponse

api_key_header: APIKeyQuery = APIKeyQuery(name="x-api-key", auto_error=False)
api_key_query: APIKeyHeader = APIKeyHeader(name="x-api-key", auto_error=False)


class GetApiKey:

    def __init__(self):
        self.request: Optional[Request] = None
        self.api_key: Optional[str] = None
        self.criadex: Optional[CriadexSDK] = None

    @abstractmethod
    async def execute(self) -> str:
        """Overridable check"""
        raise NotImplementedError

    @classmethod
    def handle_no_auth(cls, request: Request, _exc: HTTPException) -> JSONResponse:
        """Handler for failure to authenticate"""

        # Get the submitted key
        submitted: str = (
                request.headers.get(api_key_header.model.name) or
                request.query_params.get(api_key_query.model.name)
        )

        # Don't pass request object, we never send stacktrace for this
        return JSONResponse(
            status_code=401,
            content=UnauthorizedResponse(
                message=(
                    f"Your key is unauthorized for this action."
                    if submitted else
                    "You did not send an API key, and are unauthorized for this action."
                ),
                detail=str(_exc.detail) if _exc.detail else None
            ).dict()
        )

    @classmethod
    def _resolve_api_key(
            cls,
            api_key: str,
    ) -> Optional[str]:
        """Pre-process the API key string"""

        if not api_key or api_key == "None":
            return None

        return api_key

    async def get_auth(self) -> AuthCheckRoute.Response:

        response: AuthCheckRoute.Response = await self.criadex.auth.check(
            api_key=self.api_key
        )

        if not response.status == 200:
            logging.error("Failed to check API key. Received payload: " + str(response))
            raise BadAPIKeyException(
                status_code=500,
                detail="Failed to check API key due to an error!"
            )

        return response

    async def get_group_auth(self, group_name: str) -> GroupAuthCheckRoute.Response:

        response: AuthCheckRoute.Response = await self.criadex.group_auth.check(
            group_name=group_name,
            api_key=self.api_key
        )

        if not response.status == 200:
            logging.error("Failed to check API key. Received payload: " + str(response))
            raise BadAPIKeyException(
                status_code=500,
                detail="Failed to check API key due to an error!"
            )

        return response

    async def __call__(
            self,
            request: Request,
            query_api_key: str = Security(api_key_query),
            header_api_key: str = Security(api_key_header)
    ) -> str:
        """Check the API key"""

        # Retrieve the API key
        self.api_key = (
                self._resolve_api_key(query_api_key) or self._resolve_api_key(header_api_key)
        )

        self.criadex: CriadexSDK = request.app.criadex
        self.request: Request = request

        # Make sure an API key was passed
        if self.api_key is None:
            raise BadAPIKeyException(
                status_code=401,
                detail="No API key was sent for this action."
            )

        # Handle errors
        return await self.execute()


class BadAPIKeyException(HTTPException):
    """Exception raised when an invalid API key is sent"""
