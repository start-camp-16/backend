from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse, operation_id="health")
def health(session: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    session.execute(text("SELECT 1"))
    return HealthResponse()
