from unittest.mock import AsyncMock, patch

import pytest

from criaparse.client import CriaParse


@pytest.mark.asyncio
async def test_poll_keeps_finished_job_available_for_repeated_reads():
    parser_client = CriaParse.__new__(CriaParse)
    parser_client._redis = object()

    finished_job = type("JobDataStub", (), {"finished": True})()

    with patch("criaparse.client.JobData.from_redis", new=AsyncMock(return_value=finished_job)) as from_redis:
        first = await parser_client.poll("job-1")
        second = await parser_client.poll("job-1")

    assert first is finished_job
    assert second is finished_job
    assert from_redis.await_count == 2


@pytest.mark.asyncio
async def test_poll_returns_unfinished_job_data_without_side_effects():
    parser_client = CriaParse.__new__(CriaParse)
    parser_client._redis = object()

    unfinished_job = type("JobDataStub", (), {"finished": False})()

    with patch("criaparse.client.JobData.from_redis", new=AsyncMock(return_value=unfinished_job)) as from_redis:
        result = await parser_client.poll("job-2")

    assert result is unfinished_job
    from_redis.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_returns_none_for_missing_job():
    parser_client = CriaParse.__new__(CriaParse)
    parser_client._redis = object()

    with patch("criaparse.client.JobData.from_redis", new=AsyncMock(return_value=None)) as from_redis:
        result = await parser_client.poll("missing-job")

    assert result is None
    from_redis.assert_awaited_once()
