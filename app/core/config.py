import os
from typing import Optional

from dotenv import load_dotenv

from .schemas import AppMode, check_env_path, CriadexCredentials, RedisCredentials

ENV_PATH: str = os.environ.get('ENV_PATH', "../.env")
ENV_LOADED: bool = load_dotenv(dotenv_path=check_env_path(ENV_PATH))

APP_MODE: AppMode = AppMode[os.environ.get('APP_API_MODE', AppMode.TESTING.name)]
APP_HOST: str = "0.0.0.0"
APP_PORT: int = int(os.environ.get('APP_API_PORT', 25574))
APP_TITLE: str = "CriaParse ⚙️"
APP_VERSION = "1.0.0"
DOCS_URL: str = "/"

# Initial Auth Key
API_KEY: Optional[str] = os.environ.get("API_KEY")

# Search Rate Limit
SEARCH_INDEX_LIMIT_MINUTE: str = (os.environ.get("SEARCH_INDEX_LIMIT_MINUTE") or "30") + "/minute"
SEARCH_INDEX_LIMIT_HOUR: str = (os.environ.get("SEARCH_INDEX_LIMIT_HOUR") or "250") + "/hour"
SEARCH_INDEX_LIMIT_DAY: str = (os.environ.get("SEARCH_INDEX_LIMIT_DAY") or "1500") + "/day"

# Query Rate Limit
QUERY_MODEL_RATE_LIMIT_MINUTE: str = SEARCH_INDEX_LIMIT_MINUTE
QUERY_MODEL_RATE_LIMIT_HOUR: str = SEARCH_INDEX_LIMIT_HOUR
QUERY_MODEL_RATE_LIMIT_DAY: str = SEARCH_INDEX_LIMIT_DAY

# Swagger Config
SWAGGER_TITLE: str = "CriaParse API"
SWAGGER_FAVICON: str = "https://i.imgur.com/9XOI3qg.png"
SWAGGER_DESCRIPTION = f"""
<img width="40px" src="{SWAGGER_FAVICON}"/><br/><br/>
An asynchronous REST API for RAG data ingestion.
"""

# Redis Config
REDIS_CREDENTIALS: RedisCredentials = RedisCredentials(
    host=os.environ.get("REDIS_HOST"),
    port=os.environ.get("REDIS_PORT"),
    username=os.environ.get("REDIS_USERNAME"),
    password=os.environ.get("REDIS_PASSWORD"),
)

CRIADEX_CREDENTIALS: CriadexCredentials = CriadexCredentials(
    api_base=os.environ["CRIADEX_API_BASE"],
    api_key=os.environ["CRIADEX_API_KEY"]
)
