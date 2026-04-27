from fastapi import APIRouter

from ..models.schemas import ChatRequest, ChatResponse
from ..providers.router import route

router = APIRouter()


@router.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await route(request)
