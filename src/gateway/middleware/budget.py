from datetime import datetime

from fastapi import HTTPException
from redis.asyncio import Redis

from ..config.loader import Team

# Cost in USD per 1 million tokens: (input, output)
MODEL_COSTS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "claude-haiku-4-5": (0.80, 4.00),
    "claude-sonnet-4": (3.00, 15.00),
}

DEFAULT_COST = (1.00, 5.00)  # fallback for unknown models


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    # find the first key that the model name starts with
    costs = next(
        (v for k, v in MODEL_COSTS.items() if model.startswith(k)), DEFAULT_COST
    )
    input_cost = (input_tokens / 1_000_000) * costs[0]
    output_cost = (output_tokens / 1_000_000) * costs[1]
    return round(input_cost + output_cost, 6)


def _month_key(team_id: str) -> str:
    now = datetime.utcnow()
    return f"budget:{team_id}:{now.year}-{now.month:02d}"


async def check_and_record_spend(team: Team, cost: float, redis: Redis) -> bool:
    key = _month_key(team.id)
    current = await redis.get(key)
    total_spent = round(float(current or 0) + cost, 6)

    warning_threshold = team.budget.monthly_usd * team.budget.warning_threshold
    at_warning = total_spent >= warning_threshold

    if total_spent >= team.budget.monthly_usd:
        raise HTTPException(
            status_code=402,
            detail=f"monthly budget cap of ${team.budget.monthly_usd} exceeded",
        )

    # 32-day expiry so the key outlasts the month slightly, then auto-cleans
    await redis.set(key, total_spent, ex=60 * 60 * 24 * 32)

    return at_warning
