from typing import Any, Protocol, cast

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError


class ProviderRateLimited(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


class ChatProvider(Protocol):
    def answer(self, *, instructions: str, input_messages: list[dict[str, str]]) -> str: ...


class OpenAIChatProvider:
    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def answer(self, *, instructions: str, input_messages: list[dict[str, str]]) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=cast(Any, input_messages),
            )
            return response.output_text
        except RateLimitError as exc:
            raise ProviderRateLimited from exc
        except (APITimeoutError, APIConnectionError, APIError) as exc:
            raise ProviderUnavailable from exc
