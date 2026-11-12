from __future__ import annotations

from typing import Any

import httpx
import pytest
from sakuramedia_javdb_ranking import client as client_module
from sakuramedia_javdb_ranking.client import JavdbClient, JavdbRequestError


class FakeI18n:
    def t(self, key: str, default: str | None = None, **params: Any) -> str:
        template = default if default is not None else key
        try:
            return template.format(**params)
        except (KeyError, ValueError):
            return template


def _client(handler, *, max_retries: int = 0) -> JavdbClient:
    return JavdbClient(
        host="example.com",
        timeout_seconds=5,
        max_retries=max_retries,
        i18n=FakeI18n(),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _payload(numbers: list[str]) -> dict[str, Any]:
    return {
        "success": 1,
        "data": {"movies": [{"number": number} for number in numbers]},
    }


def test_rank_request_is_anonymous_and_signed():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        seen["headers"] = request.headers
        return httpx.Response(200, json=_payload(["ABP-001", "ABP-002"]))

    client = _client(handler)
    assert client.get_rank_numbers(video_type="0", period="daily") == [
        "ABP-001",
        "ABP-002",
    ]
    assert seen["path"] == "/api/v1/rankings"
    assert seen["params"] == {"type": "0", "period": "daily"}
    assert "authorization" not in seen["headers"]
    assert seen["headers"]["jdsignature"].count(".") == 2
    assert seen["headers"]["accept-language"] == "zh-TW"


def test_playback_request_uses_filter_and_period():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=_payload(["ABP-001"]))

    client = _client(handler)
    assert client.get_playback_rank_numbers(
        filter_by="high_score", period="weekly"
    ) == ["ABP-001"]
    assert seen == {
        "path": "/api/v1/rankings/playback",
        "params": {"filter_by": "high_score", "period": "weekly"},
    }


def test_business_error_is_raised():
    client = _client(
        lambda request: httpx.Response(
            200,
            json={"success": 0, "action": "JWTVerificationError"},
        )
    )
    with pytest.raises(JavdbRequestError, match="JWTVerificationError"):
        client.get_rank_numbers(video_type="0", period="daily")


def test_missing_movies_is_raised():
    client = _client(
        lambda request: httpx.Response(200, json={"success": 1, "data": {}})
    )
    with pytest.raises(JavdbRequestError, match="data.movies"):
        client.get_playback_rank_numbers(filter_by="all", period="daily")


def test_429_is_retried(monkeypatch):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429)
        return httpx.Response(200, json=_payload(["ABP-001"]))

    monkeypatch.setattr(client_module.time, "sleep", lambda _seconds: None)
    client = _client(handler, max_retries=1)
    assert client.get_rank_numbers(video_type="3", period="monthly") == ["ABP-001"]
    assert calls == 2
