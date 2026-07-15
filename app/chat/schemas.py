from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

TrimmedMessage = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]
TrimmedHistoryContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class StrictChatModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatMessage(StrictChatModel):
    role: ChatRole
    content: TrimmedHistoryContent


class ChatRequest(StrictChatModel):
    message: TrimmedMessage
    history: list[ChatMessage] = Field(default_factory=list, max_length=10)


class LocationSource(BaseModel):
    type: Literal["location"] = "location"
    content_id: str
    title: str
    category: str
    district: str
    address: str | None


class PostSource(BaseModel):
    type: Literal["post"] = "post"
    post_id: int
    title: str
    district: str
    prefix: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[LocationSource | PostSource]
