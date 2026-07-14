from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas import Pagination

TrimmedTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
TrimmedPostContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
]
TrimmedCommentContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]
Password = Annotated[str, StringConstraints(min_length=4, max_length=20)]


class PostTag(StrEnum):
    TOURISM = "관광"
    FOOD = "맛집"
    CULTURE = "문화"
    EVENT = "행사"
    ACCOMMODATION = "숙박"
    SHOPPING = "쇼핑"
    FREE = "자유"


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PostCreate(StrictRequest):
    tag: PostTag
    title: TrimmedTitle
    content: TrimmedPostContent
    password: Password


class PostUpdate(StrictRequest):
    password: Password
    tag: PostTag
    title: TrimmedTitle
    content: TrimmedPostContent


class PasswordRequest(StrictRequest):
    password: Password


class CommentCreate(StrictRequest):
    content: TrimmedCommentContent
    password: Password


class CommentUpdate(StrictRequest):
    password: Password
    content: TrimmedCommentContent


class PostSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tag: PostTag
    title: str
    created_at: datetime
    updated_at: datetime


class PostDetail(PostSummary):
    content: str


class PostListResponse(BaseModel):
    items: list[PostSummary]
    pagination: Pagination


class CommentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    content: str
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    items: list[CommentDetail]
