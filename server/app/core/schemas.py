import json
import os
from enum import Enum
from json import JSONDecodeError
from typing import Optional

from fastapi import Form
from pydantic import BaseModel
from starlette import status
from starlette.exceptions import HTTPException

from app.controllers.schemas import APIResponse, RATE_LIMIT


class AppMode(Enum):
    """
    Whether the app is loaded in production or not

    """

    TESTING = 1
    PRODUCTION = 2


class EnvNotFoundException(FileNotFoundError):
    """Raised when the .env file cannot be found"""


def check_env_path(env_path: str) -> str:
    """
    Check if the dotenv file exists. If it doesn't, throw an error.

    :param env_path: The .env path
    :return: The path that we received originally

    """

    if not os.path.isfile(env_path):
        raise EnvNotFoundException(
            f"Failed to locate dotenv file at '{env_path}'. "
            f"Specify location with the ENV_PATH environment variable"
        )

    return env_path


class RateLimitResponse(APIResponse):
    status: int = 429
    code: RATE_LIMIT


class UnstructuredCredentials(BaseModel):
    api_base: str
    api_key: str


class CriadexCredentials(UnstructuredCredentials):
    pass


def form_metadata_converter(file_metadata: Optional[str] = Form(default=None)) -> Optional[dict]:
    try:
        return json.loads(file_metadata) if file_metadata else None
    except JSONDecodeError:
        raise HTTPException(
            detail="Invalid JSON string. Payload must be a JSON-serializable string.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
