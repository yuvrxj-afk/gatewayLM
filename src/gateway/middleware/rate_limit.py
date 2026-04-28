import time
from fastapi import HTTPException
from redis.asyncio import Redis

from ..config.loader import Team


RATE_LIMIT_SCRIPT = """
local key_tokens = KEYS[1]
local key_refill = KEYS[2]
local capacity   = tonumber(ARGV[1])
local rate       = tonumber(ARGV[2])
local now        = tonumber(ARGV[3])

local tokens     = tonumber(redis.call('GET', key_tokens) or capacity)
local last       = tonumber(redis.call('GET', key_refill) or now)

local delta      = math.floor((now - last) * rate / 60)
tokens           = math.min(capacity, tokens + delta)

if tokens < 1 then
  return 0
end

redis.call('SET', key_tokens, tokens - 1, 'EX', 120)
redis.call('SET', key_refill, now, 'EX', 120)
return 1
"""


async def check_rate_limit(team: Team, redis: Redis) -> None:
    key_tokens = f"ratelimit:{team.id}:tokens"
    key_refill = f"ratelimit:{team.id}:last_refill"

    capacity = team.rate_limits.requests_per_minute
    if team.priority == "low":
        capacity = capacity // 2

    result = await redis.eval(
        RATE_LIMIT_SCRIPT,
        2,  # number of KEYS
        key_tokens,
        key_refill,
        capacity,         # ARGV[1] capacity
        capacity,         # ARGV[2] rate
        int(time.time()), # ARGV[3] now
    )

    if result == 0:
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded",
            headers={"Retry-After": "60"},
        )


async def deduct_tokens(team: Team, tokens_used: int, redis: Redis) -> None:
    key = f"ratelimit:{team.id}:tpm"
    current = await redis.get(key)
    used = int(current or 0) + tokens_used

    if used > team.rate_limits.tokens_per_minute:
        raise HTTPException(
            status_code=429,
            detail="token rate limit exceeded",
            headers={"Retry-After": "60"},
        )

    await redis.set(key, used, ex=60)
