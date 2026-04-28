"""
Circuit breaker — three states stored in Redis:

  CLOSED    → normal, requests go through
  OPEN      → provider is failing, requests blocked immediately
  HALF_OPEN → cooldown elapsed, sending one test request

State machine:
  CLOSED  --[N failures in M seconds]--> OPEN
  OPEN    --[cooldown elapsed]---------> HALF_OPEN
  HALF_OPEN --[success]-----------------> CLOSED
  HALF_OPEN --[failure]-----------------> OPEN
"""

import time
from redis.asyncio import Redis

FAILURE_THRESHOLD = 5       # failures before opening
FAILURE_WINDOW_SEC = 60     # rolling window for failure count
COOLDOWN_SEC = 30           # how long to stay OPEN before trying again

CLOSED    = "closed"
OPEN      = "open"
HALF_OPEN = "half-open"


def _keys(provider: str) -> tuple[str, str, str]:
    base = f"circuit:{provider}"
    return f"{base}:state", f"{base}:failures", f"{base}:opened_at"


async def get_state(provider: str, redis: Redis) -> str:
    state_key, _, opened_at_key = _keys(provider)
    state = await redis.get(state_key)
    if state is None:
        return CLOSED

    state = state.decode()

    if state == OPEN:
        opened_at = await redis.get(opened_at_key)
        if opened_at and (time.time() - float(opened_at)) >= COOLDOWN_SEC:
            await redis.set(state_key, HALF_OPEN)
            return HALF_OPEN

    return state


async def record_success(provider: str, redis: Redis) -> None:
    state_key, failures_key, opened_at_key = _keys(provider)
    await redis.set(state_key, CLOSED)
    await redis.delete(failures_key, opened_at_key)


async def record_failure(provider: str, redis: Redis) -> None:
    state_key, failures_key, opened_at_key = _keys(provider)

    failures = await redis.incr(failures_key)
    await redis.expire(failures_key, FAILURE_WINDOW_SEC)

    if failures >= FAILURE_THRESHOLD:
        await redis.set(state_key, OPEN)
        await redis.set(opened_at_key, time.time())
