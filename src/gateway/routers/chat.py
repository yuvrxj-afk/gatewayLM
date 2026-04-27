from fastapi import APIRouter, Depends
from redis.asyncio import Redis, from_url

from ..config.loader import Team
from ..config.settings import settings
from ..middleware.auth import get_current_team
from ..middleware.rate_limit import check_rate_limit, deduct_tokens
from ..models.schemas import ChatRequest, ChatResponse
from ..providers.router import route

router = APIRouter()


async def get_redis() -> Redis:
    return from_url(settings.redis_url)


@router.post("/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    team: Team = Depends(get_current_team),
    redis: Redis = Depends(get_redis),
) -> ChatResponse:
    await check_rate_limit(team, redis)
    response = await route(request, team.system_prompt)
    total_tokens = response.usage.input_tokens + response.usage.output_tokens
    await deduct_tokens(team, total_tokens, redis)

    return response
