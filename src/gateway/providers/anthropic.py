import time
import httpx
from ..models.schemas import ChatRequest, ChatResponse, UsageStats


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


async def complete(request: ChatRequest, api_key: str) -> ChatResponse:

    system_messages = [m for m in request.messages if m.role == "system"]
    non_system = [m for m in request.messages if m.role != "system"]

    payload = {
        "model": request.model,
        "messages": [m.model_dump() for m in non_system],
        "max_tokens": request.max_tokens or 1024,
    }

    if request.temperature is not None:
        payload["temperature"] = request.temperature

    if system_messages:
        payload["system"] = system_messages[0].content

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }

    start = time.monotonic()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
        response.raise_for_status()

    elapsed_ms = int((time.monotonic() - start) * 1000)

    data = response.json()

    return ChatResponse(
        id=data["id"],
        model_requested=request.model,
        model_served=data["model"],
        provider="anthropic",
        content=data["content"][0]["text"],
        usage=UsageStats(
            input_tokens=data["usage"]["input_tokens"],
            output_tokens=data["usage"]["output_tokens"],
        ),
        latency_ms=elapsed_ms,
    )
