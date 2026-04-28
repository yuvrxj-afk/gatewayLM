"""
Mock providers for offline integration testing.

Exposes minimal endpoints compatible with our adapters:
  - OpenAI:    POST /v1/chat/completions
  - Anthropic: POST /v1/messages
  - Ollama:    POST /api/chat

Also supports failure injection:
  - Set env FAIL_OPENAI=1 / FAIL_ANTHROPIC=1 / FAIL_OLLAMA=1 to force 503
"""

import os
import time
import uuid

from fastapi import FastAPI, Header, HTTPException, Response

app = FastAPI(title="GatewayLM Mock Providers")


def _maybe_fail(env_key: str) -> None:
    if os.getenv(env_key, "0") == "1":
        raise HTTPException(status_code=503, detail=f"{env_key} forced failure")


@app.post("/v1/chat/completions")
async def openai_chat_completions(authorization: str | None = Header(default=None)):
    _maybe_fail("FAIL_OPENAI")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    # Deterministic response structure matching OpenAI adapter expectations
    return {
        "id": f"chatcmpl_{uuid.uuid4().hex}",
        "model": "mock-gpt",
        "choices": [{"message": {"role": "assistant", "content": "mock: openai ok"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7},
    }


@app.post("/v1/messages")
async def anthropic_messages(
    x_api_key: str | None = Header(default=None),
    anthropic_version: str | None = Header(default=None),
):
    _maybe_fail("FAIL_ANTHROPIC")
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing x-api-key")
    if not anthropic_version:
        raise HTTPException(status_code=400, detail="missing anthropic-version")
    return {
        "id": f"msg_{uuid.uuid4().hex}",
        "model": "mock-claude",
        "content": [{"type": "text", "text": "mock: anthropic ok"}],
        "usage": {"input_tokens": 4, "output_tokens": 9},
    }


@app.post("/api/chat")
async def ollama_chat():
    _maybe_fail("FAIL_OLLAMA")
    now = time.time()
    return {
        "model": "mock-ollama",
        "created_at": now,
        "message": {"role": "assistant", "content": "mock: ollama ok"},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 3,
        "eval_count": 6,
    }


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


@app.post("/admin/fail/{provider}/{value}")
async def set_fail(provider: str, value: int) -> dict:
    env = {
        "openai": "FAIL_OPENAI",
        "anthropic": "FAIL_ANTHROPIC",
        "ollama": "FAIL_OLLAMA",
    }.get(provider)
    if not env:
        raise HTTPException(status_code=400, detail="unknown provider")
    os.environ[env] = "1" if value else "0"
    return {"provider": provider, "fail": os.environ[env]}

