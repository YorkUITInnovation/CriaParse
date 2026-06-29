import os
from pathlib import Path

import pytest

# Ensure app.core.config can load dotenv during import in test context.
os.environ.setdefault("ENV_PATH", str((Path(__file__).resolve().parents[1] / ".env").resolve()))

from app.core.security.get_api_key import GetApiKey
from app.core.security.handlers.master import GetApiKeyMaster
from app.core.security.handlers.any import GetApiKeyAny


class _DummyAuth:
    def __init__(self, response=None, exc=None):
        self.response = response if response is not None else {"status": 200}
        self.exc = exc
        self.calls = 0

    async def check(self, **kwargs):
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return self.response


class _DummySDK:
    def __init__(self, auth=None, group_auth=None):
        self.auth = auth if auth is not None else _DummyAuth()
        self.group_auth = group_auth if group_auth is not None else _DummyAuth()


@pytest.mark.asyncio
async def test_get_auth_uses_cache_after_success(monkeypatch):
    monkeypatch.setattr("app.core.config.API_KEY_AUTH_CACHE_TTL", 60)

    key_checker = GetApiKey()
    key_checker.api_key = "k1"
    key_checker.criadex = _DummySDK(auth=_DummyAuth(response={"status": 200}))

    # First call should reach Criadex.
    first = await key_checker.get_auth()
    assert first["status"] == 200
    assert key_checker.criadex.auth.calls == 1

    # Second call should be served from cache.
    second = await key_checker.get_auth()
    assert second["status"] == 200
    assert second.get("cached") is True
    assert key_checker.criadex.auth.calls == 1


@pytest.mark.asyncio
async def test_get_auth_allows_cached_fallback_on_transient_error(monkeypatch):
    monkeypatch.setattr("app.core.config.API_KEY_AUTH_CACHE_TTL", 60)

    auth = _DummyAuth(response={"status": 200})
    key_checker = GetApiKey()
    key_checker.api_key = "k2"
    key_checker.criadex = _DummySDK(auth=auth)

    # Seed cache from initial success.
    first = await key_checker.get_auth()
    assert first["status"] == 200
    assert auth.calls == 1

    # Force backend auth failure; cached key should still pass.
    auth.exc = RuntimeError("temporary network issue")
    cached = await key_checker.get_auth()
    assert cached["status"] == 200
    assert cached.get("cached") is True
    assert auth.calls == 1


@pytest.mark.asyncio
async def test_get_group_auth_uses_cache_after_success(monkeypatch):
    monkeypatch.setattr("app.core.config.API_KEY_AUTH_CACHE_TTL", 60)

    group_auth = _DummyAuth(response={"status": 200})
    key_checker = GetApiKey()
    key_checker.api_key = "k3"
    key_checker.criadex = _DummySDK(group_auth=group_auth)

    first = await key_checker.get_group_auth("g1")
    assert first["status"] == 200
    assert group_auth.calls == 1

    second = await key_checker.get_group_auth("g1")
    assert second["status"] == 200
    assert second.get("cached") is True
    assert group_auth.calls == 1


@pytest.mark.asyncio
async def test_master_handler_works_with_cached_auth_payload(monkeypatch):
    """Regression: cached auth must preserve 'master' to avoid false 401."""
    monkeypatch.setattr("app.core.config.API_KEY_AUTH_CACHE_TTL", 60)

    auth = _DummyAuth(response={"status": 200, "master": True, "authorized": True})
    handler = GetApiKeyMaster()
    handler.api_key = "master-key"
    handler.criadex = _DummySDK(auth=auth)

    # First call hits backend and seeds cache.
    key1 = await handler.execute()
    assert key1 == "master-key"
    assert auth.calls == 1

    # Simulate transient backend issue; second call should use cache and still pass.
    auth.exc = RuntimeError("temporary auth outage")
    key2 = await handler.execute()
    assert key2 == "master-key"
    assert auth.calls == 1


@pytest.mark.asyncio
async def test_any_handler_works_with_cached_auth_payload(monkeypatch):
    """Regression: cached auth payload should continue to satisfy Any handler checks."""
    monkeypatch.setattr("app.core.config.API_KEY_AUTH_CACHE_TTL", 60)

    auth = _DummyAuth(response={"status": 200, "master": True, "authorized": True})
    handler = GetApiKeyAny()
    handler.api_key = "authorized-key"
    handler.criadex = _DummySDK(auth=auth)
    handler.request = None

    key1 = await handler.execute()
    assert key1 == "authorized-key"
    assert auth.calls == 1

    auth.exc = RuntimeError("temporary auth outage")
    key2 = await handler.execute()
    assert key2 == "authorized-key"
    assert auth.calls == 1
