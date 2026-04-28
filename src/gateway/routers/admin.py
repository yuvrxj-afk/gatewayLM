from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis, from_url
from pydantic import BaseModel

from ..config.loader import load_config
from ..config.settings import settings
from ..middleware.budget import _month_key

router = APIRouter(prefix="/admin")


async def get_redis() -> Redis:
    return from_url(settings.redis_url)


class TeamStatus(BaseModel):
    team_id: str
    name: str
    priority: str
    requests_per_minute: int
    tokens_per_minute: int
    monthly_budget_usd: float
    current_month_spend_usd: float
    budget_utilization_pct: float
    current_rpm_tokens: int | None
    current_tpm_used: int | None


@router.get("/teams", response_model=list[TeamStatus])
async def list_teams(redis: Redis = Depends(get_redis)) -> list[TeamStatus]:
    config = load_config()
    result = []

    for team in config.teams:
        spend_raw = await redis.get(_month_key(team.id))
        tpm_raw   = await redis.get(f"ratelimit:{team.id}:tpm")
        rpm_raw   = await redis.get(f"ratelimit:{team.id}:tokens")

        spend = float(spend_raw or 0)
        utilization = round((spend / team.budget.monthly_usd) * 100, 2)

        result.append(TeamStatus(
            team_id=team.id,
            name=team.name,
            priority=team.priority,
            requests_per_minute=team.rate_limits.requests_per_minute,
            tokens_per_minute=team.rate_limits.tokens_per_minute,
            monthly_budget_usd=team.budget.monthly_usd,
            current_month_spend_usd=spend,
            budget_utilization_pct=utilization,
            current_rpm_tokens=int(rpm_raw) if rpm_raw else None,
            current_tpm_used=int(tpm_raw) if tpm_raw else None,
        ))

    return result


@router.get("/teams/{team_id}", response_model=TeamStatus)
async def get_team(team_id: str, redis: Redis = Depends(get_redis)) -> TeamStatus:
    config = load_config()
    team = next((t for t in config.teams if t.id == team_id), None)

    if not team:
        raise HTTPException(status_code=404, detail=f"team '{team_id}' not found")

    spend_raw = await redis.get(_month_key(team.id))
    tpm_raw   = await redis.get(f"ratelimit:{team.id}:tpm")
    rpm_raw   = await redis.get(f"ratelimit:{team.id}:tokens")

    spend = float(spend_raw or 0)

    return TeamStatus(
        team_id=team.id,
        name=team.name,
        priority=team.priority,
        requests_per_minute=team.rate_limits.requests_per_minute,
        tokens_per_minute=team.rate_limits.tokens_per_minute,
        monthly_budget_usd=team.budget.monthly_usd,
        current_month_spend_usd=spend,
        budget_utilization_pct=round((spend / team.budget.monthly_usd) * 100, 2),
        current_rpm_tokens=int(rpm_raw) if rpm_raw else None,
        current_tpm_used=int(tpm_raw) if tpm_raw else None,
    )


@router.delete("/teams/{team_id}/limits")
async def reset_limits(team_id: str, redis: Redis = Depends(get_redis)) -> dict:
    """Reset rate limit counters for a team (useful after adjusting config)."""
    config = load_config()
    if not any(t.id == team_id for t in config.teams):
        raise HTTPException(status_code=404, detail=f"team '{team_id}' not found")

    await redis.delete(
        f"ratelimit:{team_id}:tokens",
        f"ratelimit:{team_id}:last_refill",
        f"ratelimit:{team_id}:tpm",
    )
    return {"reset": True, "team_id": team_id}
