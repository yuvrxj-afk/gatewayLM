from fastapi import HTTPException
import pytest
import fakeredis.aioredis

from src.gateway.config.loader import Budget, RateLimits, Team
from src.gateway.middleware.rate_limit import check_rate_limit


@pytest.fixture
def redis():
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def team():
    return Team(
        id="test-team",
        name="Test Team",
        api_key="test-key",
        allowed_models=["gpt-4o-mini"],
        rate_limits=RateLimits(requests_per_minute=2, tokens_per_minute=1000),
        budget=Budget(monthly_usd=10.0, warning_threshold=0.8),
        priority="standard",
    )


@pytest.mark.asyncio
async def test_first_request_passes(team, redis):
    await check_rate_limit(team, redis)


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_limit(team, redis):
    await check_rate_limit(team, redis)
    await check_rate_limit(team, redis)

    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(team, redis)

    assert exc_info.value.status_code == 429
