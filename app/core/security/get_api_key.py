import logging
import time
from abc import abstractmethod
from typing import Optional

from CriadexSDK.ragflow_sdk import RAGFlowSDK as CriadexSDK
from fastapi import Security, HTTPException
from fastapi.security import APIKeyQuery, APIKeyHeader
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.controllers.schemas import UnauthorizedResponse
from app.core import config

api_key_header: APIKeyQuery = APIKeyQuery(name="x-api-key", auto_error=False)
api_key_query: APIKeyHeader = APIKeyHeader(name="x-api-key", auto_error=False)


class GetApiKey:

    _auth_cache = {}
    _group_auth_cache = {}

    @staticmethod
    def _normalize_auth_response(response) -> dict:
        """Normalize SDK auth responses into a consistent dict payload."""
        if isinstance(response, dict):
            return dict(response)

        payload = {
            "status": getattr(response, "status", 200),
        }

        if hasattr(response, "master"):
            payload["master"] = bool(getattr(response, "master"))
        if hasattr(response, "authorized"):
            payload["authorized"] = bool(getattr(response, "authorized"))

        return payload

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

    async def get_auth(self):

        now = time.time()
        cache_entry = self._auth_cache.get(self.api_key)
        if cache_entry and float(cache_entry.get("expires_at", 0)) > now:
            cached_payload = dict(cache_entry.get("response", {}))
            cached_payload["cached"] = True
            return cached_payload

        try:
            response = await self.criadex.auth.check(
                api_key=self.api_key
            )
        except Exception as exc:
            if cache_entry and float(cache_entry.get("expires_at", 0)) > now:
                logging.warning(
                    "Transient auth.check failure for cached key; allowing cached auth: %s",
                    exc
                )
                cached_payload = dict(cache_entry.get("response", {}))
                cached_payload["cached"] = True
                return cached_payload
            raise

        normalized = self._normalize_auth_response(response)
        status = normalized.get("status", 200)

        if status != 200:
            logging.error("Failed to check API key. Received payload: " + str(normalized))
            raise BadAPIKeyException(
                status_code=500,
                detail="Failed to check API key due to an error!"
            )

        self._auth_cache[self.api_key] = {
            "expires_at": now + max(1, int(config.API_KEY_AUTH_CACHE_TTL)),
            "response": normalized,
        }

        return normalized

    async def get_group_auth(self, group_name: str):

        cache_key = f"{self.api_key}:{group_name}"
        now = time.time()
        cache_entry = self._group_auth_cache.get(cache_key)
        if cache_entry and float(cache_entry.get("expires_at", 0)) > now:
            cached_payload = dict(cache_entry.get("response", {}))
            cached_payload["cached"] = True
            return cached_payload

        try:
            response = await self.criadex.group_auth.check(
                group_name=group_name,
                api_key=self.api_key
            )
        except Exception as exc:
            if cache_entry and float(cache_entry.get("expires_at", 0)) > now:
                logging.warning(
                    "Transient group_auth.check failure for cached key/group; allowing cached auth: %s",
                    exc
                )
                cached_payload = dict(cache_entry.get("response", {}))
                cached_payload["cached"] = True
                return cached_payload
            raise

        normalized = self._normalize_auth_response(response)
        status = normalized.get("status", 200)

        if status != 200:
            logging.error("Failed to check API key. Received payload: " + str(normalized))
            raise BadAPIKeyException(
                status_code=500,
                detail="Failed to check API key due to an error!"
            )

        self._group_auth_cache[cache_key] = {
            "expires_at": now + max(1, int(config.API_KEY_AUTH_CACHE_TTL)),
            "response": normalized,
        }

        return normalized

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
