import time
import uuid
import httpx

from ..models.schemas import ChatRequest, ChatResponse, UsageStats


async def complete(request: ChatRequest, base_url: str) -> ChatResponse:

    payload = {
        "model": request.model,
        "messages": [m.model_dump() for m in request.messages],
        "stream": False,
    }

    if request.temperature is not None:
        payload["temperature"] = request.temperature

    headers = {
        "Content-Type": "application/json",
    }

    start = time.monotonic()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{base_url}/api/chat", json=payload, headers=headers)
        response.raise_for_status()

    elapsed_ms = int((time.monotonic() - start) * 1000)

    data = response.json()

    return ChatResponse(
        id=str(uuid.uuid4()),
        model_requested=request.model,
        model_served=data["model"],
        provider="ollama",
        content=data["message"]["content"],
        usage=UsageStats(
            input_tokens=data["prompt_eval_count"],
            output_tokens=data["eval_count"],
        ),
        latency_ms=elapsed_ms,
    )
