import time

from fastapi import APIRouter, Depends, Response
from redis.asyncio import Redis, from_url

from ..middleware.budget import calculate_cost, check_and_record_spend
from ..config.loader import Team
from ..config.settings import settings
from ..middleware.auth import get_current_team
from ..middleware.rate_limit import check_rate_limit, deduct_tokens
from ..models.schemas import ChatRequest, ChatResponse
from ..observability import cost_total, request_latency, requests_total, tokens_total
from ..providers.router import route

router = APIRouter()


async def get_redis() -> Redis:
    return from_url(settings.redis_url)


@router.post("/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_response: Response,
    team: Team = Depends(get_current_team),
    redis: Redis = Depends(get_redis),
) -> ChatResponse:
    start = time.monotonic()
    await check_rate_limit(team, redis)
    chat_response = await route(request, team.system_prompt, redis)
    elapsed = time.monotonic() - start

    total_tokens = chat_response.usage.input_tokens + chat_response.usage.output_tokens
    await deduct_tokens(team, total_tokens, redis)

    cost = calculate_cost(
        request.model, chat_response.usage.input_tokens, chat_response.usage.output_tokens
    )
    at_warning = await check_and_record_spend(team, cost, redis)

    # record metrics
    labels = {"team": team.id, "model": request.model, "provider": chat_response.provider}
    requests_total.labels(**labels, status="success").inc()
    request_latency.labels(**{k: v for k, v in labels.items()}).observe(elapsed)
    tokens_total.labels(**labels, type="input").inc(chat_response.usage.input_tokens)
    tokens_total.labels(**labels, type="output").inc(chat_response.usage.output_tokens)
    cost_total.labels(team=team.id, model=request.model).inc(cost)

    if at_warning:
        http_response.headers["X-Budget-Warning"] = (
            f"spend approaching monthly limit of ${team.budget.monthly_usd}"
        )
    return chat_response
