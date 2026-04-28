import time
import httpx
from ..models.schemas import ChatRequest, ChatResponse, UsageStats
from ..config.settings import settings


async def complete(request: ChatRequest, api_key: str) -> ChatResponse:
    openai_api_url = f"{settings.openai_base_url}/v1/chat/completions"

    payload = {
        "model": request.model,
        "messages": [m.model_dump() for m in request.messages],
    }

    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens

    if request.temperature is not None:
        payload["temperature"] = request.temperature

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    start = time.monotonic()

    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        response = await client.post(openai_api_url, json=payload, headers=headers)
        response.raise_for_status()

    elapsed_ms = int((time.monotonic() - start) * 1000)

    data = response.json()

    return ChatResponse(
        id=data["id"],
        model_requested=request.model,
        model_served=data["model"],
        provider="openai",
        content=data["choices"][0]["message"]["content"],
        usage=UsageStats(
            input_tokens=data["usage"]["prompt_tokens"],
            output_tokens=data["usage"]["completion_tokens"],
        ),
        latency_ms=elapsed_ms,
    )
