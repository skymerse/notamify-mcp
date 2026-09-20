from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

import notamify_server


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_notamify_api() -> None:
    if not os.getenv("NOTAMIFY_API_KEY"):
        pytest.skip("NOTAMIFY_API_KEY is required for the live API test")

    now = datetime.now(timezone.utc)
    client = notamify_server.NotamifyMCPClient(notamify_server.NotamifyConfig())
    try:
        result = await client.get_notams(
            locations=["KSQL"],
            starts_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ends_at=(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    finally:
        await client.close()

    assert isinstance(result.get("notams"), list)
    assert isinstance(result.get("total_count"), int)
