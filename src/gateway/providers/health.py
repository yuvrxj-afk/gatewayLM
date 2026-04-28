"""
Background health checker — runs every 30s, pings each provider,
updates Redis: health:{provider} = healthy | degraded | down
"""

import asyncio
import logging

import httpx
from redis.asyncio import Redis, from_url

from ..config.settings import settings

logger = logging.getLogger(__name__)

HEALTH_INTERVAL = 30  # seconds between checks


async def _check_openai(api_key: str) -> bool:
    if not api_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            return r.status_code == 200
    except Exception:
        return False


async def _check_anthropic(api_key: str) -> bool:
    if not api_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            return r.status_code == 200
    except Exception:
        return False


async def _check_ollama(base_url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base_url}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def run_health_checks(redis: Redis) -> None:
    """Single round of health checks — called by the background loop."""
    checks = {
        "openai":    await _check_openai(settings.openai_api_key),
        "anthropic": await _check_anthropic(settings.anthropic_api_key),
        "ollama":    await _check_ollama(settings.ollama_base_url),
    }
    for provider, healthy in checks.items():
        status = "healthy" if healthy else "down"
        await redis.set(f"health:{provider}", status, ex=120)
        logger.info("health check %s → %s", provider, status)


async def health_check_loop() -> None:
    """Background task — runs forever, checks every HEALTH_INTERVAL seconds."""
    redis = from_url(settings.redis_url)
    while True:
        try:
            await run_health_checks(redis)
        except Exception as exc:
            logger.error("health check error: %s", exc)
        await asyncio.sleep(HEALTH_INTERVAL)
