from __future__ import annotations

import asyncio
import logging
import os
import warnings
from contextlib import asynccontextmanager
from typing import Any, List, AsyncContextManager

from CriadexSDK import CriadexSDK
from fastapi import FastAPI
from redis.asyncio import Redis, from_url
from starlette.datastructures import State
from starlette.middleware.cors import CORSMiddleware

from app.controllers.__init__ import router
from criaparse.client import CriaParse
from . import config
from .middleware import StatusMiddleware
from .security.get_api_key import BadAPIKeyException, GetApiKey


class CriaParseAPI(FastAPI):
    """
    FastAPI server

    """

    ORIGINS: List[str] = [os.environ.get("APP_API_ORIGINS", "*")]

    def __init__(
            self,
            **extra: Any
    ):
        super().__init__(**extra)

        # FastAPI Setup
        self.state: State = getattr(self, 'state', State())
        self.logger: logging.Logger = logging.getLogger('uvicorn.info')
        self.loop = asyncio.get_event_loop()

        # Criadex Setup
        self.criaparse: CriaParse | None = None
        self.criadex: CriadexSDK | None = None

    @classmethod
    async def create(cls) -> CriaParseAPI:
        """
        Generate an instance of the app

        :return: Instance of the FastAPI app

        """

        # Make more stuff
        _app: CriaParseAPI = CriaParseAPI(
            docs_url=None,
            openapi_url=None,
            lifespan=cls.app_lifespan,
        )

        # Add extra bells & whistles
        _app.include_router(router)
        _app.include_handlers()
        _app.include_middlewares()

        # Disable aiomysql warnings
        logging.getLogger('asyncio').setLevel(logging.CRITICAL)
        warnings.filterwarnings('ignore', module='aiomysql')

        return _app

    def include_handlers(self) -> None:
        """
        Include API handlers

        :return: None

        """

        self.add_exception_handler(BadAPIKeyException, GetApiKey.handle_no_auth)

    def include_middlewares(self) -> None:
        """
        Include CORS handling

        :return: None

        """

        self.add_middleware(
            CORSMiddleware,
            allow_origins=self.ORIGINS,
            allow_credentials=True,
            allow_methods=self.ORIGINS,
            allow_headers=self.ORIGINS,
        )

        self.add_middleware(
            StatusMiddleware
        )

    async def preflight_checks(self) -> bool:
        """
        Run preflight checks to confirm app is ready to "fly"

        :return: Whether to kill the app startup

        """

        preflight_failed: bool = False

        # Check if in docker
        if os.environ.get('IN_DOCKER'):
            self.logger.info("Application loaded within a Docker container.")

        # Check if .env files loaded
        if config.ENV_LOADED:
            self.logger.info("Loaded '.env' configuration file with environment variables.")

        # Check if successful
        if preflight_failed:
            self.logger.error('Application failed preflight checks and will not be able to run.')
            return False

        return True

    @staticmethod
    @asynccontextmanager
    async def app_lifespan(criaparse_api: CriaParseAPI) -> AsyncContextManager[None]:
        """
        Handle the lifespan of the app

        :return: Context manager for CriaParse

        """

        # Preflight Checks
        if not await criaparse_api.preflight_checks():
            exit()

        # Create the Criadex SDK
        criadex_sdk: CriadexSDK = CriadexSDK(
            api_base=config.CRIADEX_CREDENTIALS.api_base,
            error_stacktrace=False
        )

        # Authenticate it
        await criadex_sdk.authenticate(api_key=config.CRIADEX_CREDENTIALS.api_key)

        # Get the Redis Pool
        redis_pool: Redis = await from_url(str(config.REDIS_CREDENTIALS))

        # Set the SDK and Redis pool
        criaparse_api.criadex = criadex_sdk
        criaparse_api.criaparse = CriaParse(criadex=criadex_sdk, redis=redis_pool)
        criaparse_api.criaparse.start()

        # Shutdown is after yield
        yield

        # Shut down task loop
        await criaparse_api.criaparse.close()

        # Close pools
        await redis_pool.aclose()
        # noinspection PyProtectedMember
        await criadex_sdk._httpx.aclose()

        criaparse_api.logger.info("Shutting down Criaparse...")


# Instance of the app, started by Uvicorn.
app: CriaParseAPI = asyncio.get_event_loop().run_until_complete(CriaParseAPI.create())
