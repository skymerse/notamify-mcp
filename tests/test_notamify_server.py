from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp import Client, StdioServerParameters
from mcp.types import TextContent
from pydantic import ValidationError

import notamify_server

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_NOTAMS = {
    "notams": [
        {
            "id": "notam-1",
            "icao_code": "KJFK",
            "interpretation": {
                "category": "AERODROME",
                "affected_elements": [
                    {
                        "type": "RUNWAY",
                        "identifier": "04L/22R",
                        "effect": "CLOSED",
                        "details": "Maintenance",
                    }
                ],
            },
        }
    ],
    "total_count": 1,
    "page": 1,
    "per_page": 1,
}


def test_config_reads_and_redacts_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTAMIFY_API_KEY", "test-secret")

    config = notamify_server.NotamifyConfig()

    assert config.api_key.get_secret_value() == "test-secret"
    assert config.headers["Authorization"] == "Bearer test-secret"
    assert "test-secret" not in repr(config)


def test_config_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTAMIFY_API_KEY", raising=False)

    with pytest.raises((ValueError, ValidationError), match="NOTAMIFY_API_KEY"):
        notamify_server.NotamifyConfig()


def test_query_validation_normalizes_icao_codes() -> None:
    query = notamify_server.NotamQueryParams(locations=[" kjfk ", "egll"])

    assert query.locations == ["KJFK", "EGLL"]

    with pytest.raises(ValidationError):
        notamify_server.NotamQueryParams(locations=["JFK"])


@pytest.mark.asyncio
async def test_api_client_fetches_every_page() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = int(request.url.params["page"])
        page_notams = [{"id": "one"}, {"id": "two"}] if page == 1 else [{"id": "three"}]
        return httpx.Response(
            200,
            json={
                "notams": page_notams,
                "total_count": 3,
                "page": page,
                "per_page": 30,
            },
        )

    client = notamify_server.NotamifyMCPClient(
        notamify_server.NotamifyConfig(api_key="test-secret"),
        transport=httpx.MockTransport(handler),
    )
    try:
        result = await client.get_notams(
            locations=["kjfk"],
            starts_at="2026-09-19T00:00:00Z",
            ends_at="2026-09-20T00:00:00Z",
        )
    finally:
        await client.close()

    assert [notam["id"] for notam in result["notams"]] == ["one", "two", "three"]
    assert result["total_count"] == 3
    assert result["page"] == 1
    assert result["per_page"] == 3
    assert len(requests) == 2
    assert requests[0].url.params.get_list("location") == ["KJFK"]
    assert requests[0].headers["Authorization"] == "Bearer test-secret"


@pytest.mark.asyncio
async def test_mcp_v2_protocol_and_primitives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTAMIFY_API_KEY", "test-secret")

    async def fake_get_notams(
        _self: notamify_server.NotamifyMCPClient,
        locations: list[str],
        starts_at: str | None = None,
        ends_at: str | None = None,
        notam_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        assert locations == ["KJFK"]
        assert starts_at is not None
        assert ends_at is not None
        assert notam_ids is None
        return SAMPLE_NOTAMS

    monkeypatch.setattr(
        notamify_server.NotamifyMCPClient,
        "get_notams",
        fake_get_notams,
    )

    async with Client(notamify_server.mcp, raise_exceptions=True) as client:
        assert client.protocol_version == "2026-07-28"
        assert client.server_info is not None
        assert client.server_info.name == "Notamify"
        assert client.server_info.version == notamify_server.SERVER_VERSION
        assert client.instructions == notamify_server.mcp.instructions

        tools_result = await client.list_tools()
        tools = {tool.name: tool for tool in tools_result.tools}
        assert set(tools) == {"get_notams", "get_affected_elements"}
        assert (
            tools["get_notams"].input_schema["properties"]["locations"]["type"]
            == "array"
        )
        assert "ctx" not in tools["get_notams"].input_schema["properties"]
        assert tools["get_notams"].annotations is not None
        assert tools["get_notams"].annotations.read_only_hint is True
        assert tools["get_notams"].annotations.destructive_hint is False

        notams_result = await client.call_tool(
            "get_notams",
            {"locations": ["kjfk"], "hours_from_now": 1},
        )
        assert not notams_result.is_error
        assert notams_result.structured_content == SAMPLE_NOTAMS
        assert isinstance(notams_result.content[0], TextContent)
        assert json.loads(notams_result.content[0].text) == SAMPLE_NOTAMS

        affected_result = await client.call_tool(
            "get_affected_elements",
            {"locations": ["KJFK"], "hours_from_now": 1},
        )
        assert not affected_result.is_error
        assert isinstance(affected_result.content[0], TextContent)
        assert "AIRPORT: KJFK" in affected_result.content[0].text
        assert "04L/22R" in affected_result.content[0].text

        resources_result = await client.list_resources()
        assert [str(resource.uri) for resource in resources_result.resources] == [
            "config://api"
        ]
        resource_result = await client.read_resource("config://api")
        assert "Base URL" in resource_result.contents[0].text

        prompts_result = await client.list_prompts()
        assert [prompt.name for prompt in prompts_result.prompts] == ["analyze_notams"]
        prompt_result = await client.get_prompt(
            "analyze_notams",
            {"airport_codes": "KJFK"},
        )
        assert isinstance(prompt_result.messages[0].content, TextContent)
        assert "KJFK" in prompt_result.messages[0].content.text


@pytest.mark.asyncio
async def test_server_runs_over_stdio_transport() -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "notamify_server.py")],
        cwd=PROJECT_ROOT,
        env={"NOTAMIFY_API_KEY": "test-secret"},
    )

    async with Client(server, raise_exceptions=True) as client:
        assert client.protocol_version == "2026-07-28"
        tools_result = await client.list_tools()

    assert {tool.name for tool in tools_result.tools} == {
        "get_notams",
        "get_affected_elements",
    }


@pytest.mark.asyncio
async def test_tool_reports_authentication_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTAMIFY_API_KEY", "invalid")

    async def unauthorized(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    original_init = notamify_server.NotamifyMCPClient.__init__

    def init_with_mock_transport(
        self: notamify_server.NotamifyMCPClient,
        config: notamify_server.NotamifyConfig,
    ) -> None:
        original_init(self, config, transport=httpx.MockTransport(unauthorized))

    monkeypatch.setattr(
        notamify_server.NotamifyMCPClient,
        "__init__",
        init_with_mock_transport,
    )

    async with Client(notamify_server.mcp, raise_exceptions=True) as client:
        result = await client.call_tool("get_notams", {"locations": ["KJFK"]})

    assert result.is_error
    assert isinstance(result.content[0], TextContent)
    assert "authentication failed" in result.content[0].text
    assert "unauthorized" not in result.content[0].text
