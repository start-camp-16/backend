import json
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.chat.provider import ChatProvider, ProviderRateLimited, ProviderUnavailable
from app.chat.query import parse_query
from app.chat.retrieval import retrieve_sources
from app.chat.schemas import ChatRequest, ChatResponse, LocationSource, PostSource
from app.errors import AppError

GROUNDING_INSTRUCTIONS = """당신은 서울 지역 정보 도우미입니다.
반드시 사용자 메시지와 함께 제공된 근거만 사용해 한국어로 답하세요.
근거에 없는 사실을 추측하지 마세요.
관련 근거가 없으면 정보가 부족하다고 명확히 답하세요."""


def answer_chat(
    session: Session,
    payload: ChatRequest,
    *,
    provider: ChatProvider,
    location_limit: int,
    post_limit: int,
) -> ChatResponse:
    context = retrieve_sources(
        session,
        parse_query(payload.message),
        location_limit=location_limit,
        post_limit=post_limit,
    )
    serialized_context = json.dumps(
        {
            "locations": [asdict(item) for item in context.locations],
            "posts": [asdict(item) for item in context.posts],
        },
        ensure_ascii=False,
    )
    input_messages = [
        {"role": message.role.value, "content": message.content} for message in payload.history
    ]
    input_messages.append(
        {
            "role": "user",
            "content": f"{payload.message}\n\n제공된 근거(JSON):\n{serialized_context}",
        }
    )

    try:
        answer = provider.answer(
            instructions=GROUNDING_INSTRUCTIONS,
            input_messages=input_messages,
        )
    except ProviderRateLimited as exc:
        raise AppError(
            status_code=429,
            code="CHAT_RATE_LIMITED",
            message="요청이 많습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    except ProviderUnavailable as exc:
        raise AppError(
            status_code=502,
            code="CHAT_PROVIDER_ERROR",
            message="챗봇 서비스에 연결할 수 없습니다.",
        ) from exc

    sources: list[LocationSource | PostSource] = [
        LocationSource(
            content_id=item.content_id,
            title=item.title,
            category=item.category,
            district=item.district,
            address=item.address,
        )
        for item in context.locations
    ]
    sources.extend(
        PostSource(
            post_id=item.post_id,
            title=item.title,
            district=item.district,
            prefix=item.prefix,
        )
        for item in context.posts
    )
    return ChatResponse(answer=answer, sources=sources)
