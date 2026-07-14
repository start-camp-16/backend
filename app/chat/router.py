from typing import Annotated

from fastapi import APIRouter, Depends
from openai import OpenAI
from sqlalchemy.orm import Session

from app.chat.provider import ChatProvider, OpenAIChatProvider
from app.chat.schemas import ChatRequest, ChatResponse
from app.chat.service import answer_chat
from app.config import Settings, get_settings
from app.db import get_db
from app.errors import AppError

router = APIRouter(prefix="/api")


def get_chat_provider(settings: Annotated[Settings, Depends(get_settings)]) -> ChatProvider:
    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    if not api_key:
        raise AppError(
            status_code=502,
            code="CHAT_PROVIDER_ERROR",
            message="챗봇 서비스에 연결할 수 없습니다.",
        )
    return OpenAIChatProvider(OpenAI(api_key=api_key), settings.openai_model)


@router.post("/chat", response_model=ChatResponse, operation_id="chat")
def chat(
    payload: ChatRequest,
    session: Annotated[Session, Depends(get_db)],
    provider: Annotated[ChatProvider, Depends(get_chat_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    return answer_chat(
        session,
        payload,
        provider=provider,
        location_limit=settings.chat_location_limit,
        post_limit=settings.chat_post_limit,
    )
