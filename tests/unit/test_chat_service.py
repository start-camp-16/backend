from dataclasses import dataclass, field

import pytest
from httpx import Request, Response
from openai import APITimeoutError, RateLimitError
from sqlalchemy.orm import Session

from app.chat.provider import (
    ChatProvider,
    OpenAIChatProvider,
    ProviderRateLimited,
    ProviderUnavailable,
)
from app.chat.schemas import ChatRequest
from app.chat.service import answer_chat
from app.errors import AppError
from app.models import Location, Post


@dataclass
class FakeProvider(ChatProvider):
    result: str = "근거 기반 답변"
    error: Exception | None = None
    calls: list[tuple[str, list[dict[str, str]]]] = field(default_factory=list)

    def answer(self, *, instructions: str, input_messages: list[dict[str, str]]) -> str:
        self.calls.append((instructions, input_messages))
        if self.error is not None:
            raise self.error
        return self.result


def test_service_sends_only_retrieved_evidence_and_returns_public_sources(db_session: Session):
    post = Post(
        district="강남구",
        prefix="문화",
        title="강남 전시 후기",
        content="좋았어요",
        password="1234",
    )
    db_session.add_all(
        [
            Location(
                content_id="1",
                category="문화시설",
                title="전시 문화관",
                district="강남구",
                source_order=1,
            ),
            post,
        ]
    )
    db_session.commit()
    provider = FakeProvider()

    response = answer_chat(
        db_session,
        ChatRequest(message="강남구 문화시설 전시"),
        provider=provider,
        location_limit=5,
        post_limit=5,
    )

    assert response.answer == "근거 기반 답변"
    assert response.sources[0].type == "location"
    assert response.sources[0].title == "전시 문화관"
    assert response.sources[1].model_dump() == {
        "type": "post",
        "post_id": post.id,
        "title": "강남 전시 후기",
        "district": "강남구",
        "prefix": "문화",
    }
    instructions, messages = provider.calls[0]
    assert "제공된 근거" in instructions
    assert "전시 문화관" in messages[-1]["content"]


@pytest.mark.parametrize(
    ("provider_error", "status_code", "code"),
    [
        (ProviderRateLimited(), 429, "CHAT_RATE_LIMITED"),
        (ProviderUnavailable(), 502, "CHAT_PROVIDER_ERROR"),
    ],
)
def test_service_maps_provider_errors(db_session, provider_error, status_code, code):
    with pytest.raises(AppError) as caught:
        answer_chat(
            db_session,
            ChatRequest(message="강남구 관광지"),
            provider=FakeProvider(error=provider_error),
            location_limit=5,
            post_limit=5,
        )

    assert caught.value.status_code == status_code
    assert caught.value.code == code


class FailingResponses:
    def __init__(self, error):
        self.error = error

    def create(self, **kwargs):
        raise self.error


class FailingOpenAIClient:
    def __init__(self, error):
        self.responses = FailingResponses(error)


@pytest.mark.parametrize(
    ("sdk_error", "expected_error"),
    [
        (
            RateLimitError(
                "limited",
                response=Response(
                    429, request=Request("POST", "https://api.openai.com/v1/responses")
                ),
                body=None,
            ),
            ProviderRateLimited,
        ),
        (
            APITimeoutError(Request("POST", "https://api.openai.com/v1/responses")),
            ProviderUnavailable,
        ),
    ],
)
def test_openai_adapter_maps_sdk_errors(sdk_error, expected_error):
    provider = OpenAIChatProvider(FailingOpenAIClient(sdk_error), "test-model")  # type: ignore[arg-type]

    with pytest.raises(expected_error):
        provider.answer(instructions="grounded", input_messages=[])
