from collections.abc import Generator

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from app.admin.auth import register_admin_exception_handler
from app.admin.router import router
from app.config import Settings
from app.db import get_db
from app.errors import register_exception_handlers


def create_admin_app(
    settings: Settings,
    session_factory: sessionmaker[Session],
) -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.state.settings = settings

    def get_admin_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = get_admin_db
    register_exception_handlers(app)
    register_admin_exception_handler(app)
    app.include_router(router)
    return app
