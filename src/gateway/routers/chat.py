from fastapi import APIRouter, Depends

from ..middleware.auth import get_current_team

from ..config.loader import Team

from ..models.schemas import ChatRequest, ChatResponse
from ..providers.router import route

router = APIRouter()


@router.post("/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, team: Team = Depends(get_current_team)
) -> ChatResponse:
    return await route(request, team.system_prompt)
