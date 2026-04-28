"""
Provider router — fallback chains, retry with backoff, circuit breaker.

Flow per request:
  1. Enrich with team system prompt
  2. Load fallback chain for this model tier
  3. For each provider in chain:
     a. Skip if circuit is OPEN
     b. Call provider with retry/backoff
     c. On success → record success, return
     d. On retryable error → record failure, try next provider
     e. On non-retryable error → raise immediately
"""

import asyncio
import logging

import httpx
from fastapi import HTTPException
from redis.asyncio import Redis, from_url

from ..config.loader import FallbackEntry, load_config
from ..config.settings import settings
from ..models.schemas import ChatMessage, ChatRequest, ChatResponse
from . import anthropic, ollama, openai
from .circuit_breaker import CLOSED, HALF_OPEN, get_state, record_failure, record_success

logger = logging.getLogger(__name__)

# Errors worth retrying — transient failures
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
BACKOFF_BASE = 0.5  # seconds — doubles each attempt: 0.5, 1.0, 2.0


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS
    return False


def _get_fallback_chain(model: str) -> list[FallbackEntry]:
    config = load_config()
    if model.startswith("gpt-4o-mini") or model.startswith("claude-haiku"):
        chain = config.fallback_chains.get("tier-low")
    else:
        chain = config.fallback_chains.get("tier-high")
    return chain or []


async def _call_provider(entry: FallbackEntry, request: ChatRequest) -> ChatResponse:
    if entry.provider == "openai":
        return await openai.complete(request, settings.openai_api_key)
    if entry.provider == "anthropic":
        return await anthropic.complete(request, settings.anthropic_api_key)
    if entry.provider == "ollama":
        return await ollama.complete(request, settings.ollama_base_url)
    raise ValueError(f"unknown provider: {entry.provider}")


async def _call_with_retry(
    entry: FallbackEntry,
    request: ChatRequest,
    redis: Redis,
) -> ChatResponse:
    """Call a single provider with exponential backoff. Returns response or raises."""
    for attempt in range(MAX_RETRIES):
        try:
            response = await _call_provider(entry, request)
            await record_success(entry.provider, redis)
            return response
        except Exception as exc:
            if not _is_retryable(exc):
                raise  # auth errors, content policy — don't retry, don't fallback

            await record_failure(entry.provider, redis)
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF_BASE * (2 ** attempt)
                logger.warning(
                    "provider %s attempt %d failed, retrying in %.1fs: %s",
                    entry.provider, attempt + 1, wait, exc,
                )
                await asyncio.sleep(wait)

    raise httpx.TimeoutException(f"{entry.provider} exhausted {MAX_RETRIES} retries")


async def route(
    request: ChatRequest,
    team_system_prompt: str | None = None,
    redis: Redis | None = None,
) -> ChatResponse:
    if team_system_prompt:
        system_message = ChatMessage(role="system", content=team_system_prompt)
        request = request.model_copy(
            update={"messages": [system_message] + list(request.messages)}
        )

    if redis is None:
        redis = from_url(settings.redis_url)

    chain = _get_fallback_chain(request.model)

    # If no chain configured, fall back to simple model-based dispatch
    if not chain:
        if request.model.startswith("gpt"):
            return await openai.complete(request, settings.openai_api_key)
        if request.model.startswith("claude"):
            return await anthropic.complete(request, settings.anthropic_api_key)
        if request.model.startswith("llama") or request.model.startswith("mistral"):
            return await ollama.complete(request, settings.ollama_base_url)
        raise HTTPException(status_code=400, detail=f"unknown model: {request.model}")

    last_error: Exception | None = None

    for entry in chain:
        state = await get_state(entry.provider, redis)
        if state not in (CLOSED, HALF_OPEN):
            logger.info("circuit OPEN for %s, skipping", entry.provider)
            continue

        # For the actual request, use the model from the chain entry
        chain_request = request.model_copy(update={"model": entry.model})

        try:
            return await _call_with_retry(entry, chain_request, redis)
        except Exception as exc:
            if not _is_retryable(exc):
                raise  # non-retryable — surface immediately
            last_error = exc
            logger.warning("provider %s failed, trying next in chain", entry.provider)

    raise HTTPException(
        status_code=502,
        detail=f"all providers in fallback chain failed: {last_error}",
    )
