from starlette.testclient import TestClient

from app.chat.provider import ProviderRateLimited, ProviderUnavailable
from app.chat.router import get_chat_provider
from app.config import Settings
from app.main import create_app


class FakeProvider:
    def __init__(self, result="답변", error=None):
        self.result = result
        self.error = error

    def answer(self, *, instructions, input_messages):
        if self.error is not None:
            raise self.error
        return self.result


def set_provider(client: TestClient, provider: FakeProvider) -> None:
    client.app.dependency_overrides[get_chat_provider] = lambda: provider


def test_chat_api_returns_answer_and_sources(client: TestClient):
    set_provider(client, FakeProvider(result="정보가 부족합니다."))

    response = client.post("/api/chat", json={"message": "알려줘", "history": []})

    assert response.status_code == 200
    assert response.json() == {"answer": "정보가 부족합니다.", "sources": []}


def test_chat_rate_limit_uses_contract_error(client: TestClient):
    set_provider(client, FakeProvider(error=ProviderRateLimited()))

    response = client.post("/api/chat", json={"message": "강남구 관광지"})

    assert response.status_code == 429
    assert response.json()["code"] == "CHAT_RATE_LIMITED"


def test_chat_provider_failure_uses_contract_error(client: TestClient):
    set_provider(client, FakeProvider(error=ProviderUnavailable()))

    response = client.post("/api/chat", json={"message": "강남구 관광지"})

    assert response.status_code == 502
    assert response.json()["code"] == "CHAT_PROVIDER_ERROR"


def test_chat_rejects_more_than_ten_history_items(client: TestClient):
    set_provider(client, FakeProvider())
    history = [{"role": "user", "content": "이전 질문"}] * 11

    response = client.post("/api/chat", json={"message": "질문", "history": history})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_chat_without_api_key_returns_provider_configuration_error():
    app = create_app(Settings(_env_file=None, openai_api_key=None))

    response = TestClient(app).post("/api/chat", json={"message": "강남구 관광지"})

    assert response.status_code == 502
    assert response.json()["code"] == "CHAT_PROVIDER_ERROR"
