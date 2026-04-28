import pytest
from unittest.mock import AsyncMock

import httpx
import fakeredis.aioredis

from src.gateway.models.schemas import ChatMessage, ChatRequest, ChatResponse, UsageStats
from src.gateway.providers import anthropic as anthropic_provider
from src.gateway.providers import openai as openai_provider
from src.gateway.providers.router import route


@pytest.mark.asyncio
async def test_fallback_to_anthropic_when_openai_fails(monkeypatch: pytest.MonkeyPatch):
    # Make OpenAI fail with a retryable error, and Anthropic succeed.
    request = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content="ping")],
    )

    resp = httpx.Response(503, json={"error": "forced"})
    req = httpx.Request("POST", "http://openai.test")
    openai_error = httpx.HTTPStatusError("forced", request=req, response=resp)

    monkeypatch.setattr(openai_provider, "complete", AsyncMock(side_effect=openai_error))
    monkeypatch.setattr(
        anthropic_provider,
        "complete",
        AsyncMock(
            return_value=ChatResponse(
                id="x",
                model_requested="gpt-4o-mini",
                model_served="claude-haiku-4-5-20251001",
                provider="anthropic",
                content="ok",
                usage=UsageStats(input_tokens=1, output_tokens=1),
                latency_ms=1,
            )
        ),
    )

    redis = fakeredis.aioredis.FakeRedis()
    result = await route(request, team_system_prompt=None, redis=redis)
    assert result.provider == "anthropic"

