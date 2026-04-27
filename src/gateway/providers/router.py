from fastapi import HTTPException

from ..config.settings import settings
from ..models.schemas import ChatMessage, ChatRequest, ChatResponse
from . import anthropic, ollama, openai


async def route(
    request: ChatRequest, team_system_prompt: str | None = None
) -> ChatResponse:
    if team_system_prompt:
        system_message = ChatMessage(role="system", content=team_system_prompt)
        request = request.model_copy(
            update={"messages": [system_message] + list(request.messages)}
        )

    if request.model.startswith("gpt"):
        return await openai.complete(request, settings.openai_api_key)
    if request.model.startswith("claude"):
        return await anthropic.complete(request, settings.anthropic_api_key)
    if request.model.startswith("llama") or request.model.startswith("mistral"):
        return await ollama.complete(request, settings.ollama_base_url)

    raise HTTPException(status_code=400, detail=f"unknown model: {request.model}")
