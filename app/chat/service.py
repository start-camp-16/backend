import json
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.chat.provider import ChatProvider, ProviderRateLimited, ProviderUnavailable
from app.chat.query import parse_query
from app.chat.retrieval import retrieve_sources
from app.chat.schemas import ChatRequest, ChatResponse, LocationSource, PostSource
from app.errors import AppError

GROUNDING_INSTRUCTIONS = """당신은 서울 지역 정보 도우미입니다.
한국어로 자연스럽고 도움이 되게 답하세요.
사용자 메시지와 함께 제공된 근거가 있으면 우선 활용하되, 근거가 부족하면 일반 지식을
사용해 답하거나 추천할 수 있습니다. 근거가 부족하다는 이유만으로 답변을 거절하지 마세요.
사실을 지어내지 말고 불확실한 내용은 불확실하다고 밝히세요.
영업시간, 가격, 휴무일, 행사 일정처럼 바뀔 수 있는 정보는 최신 상태라고 단정하지 말고
공식 채널을 통해 방문 전에 확인하도록 안내하세요."""


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
