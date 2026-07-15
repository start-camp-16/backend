import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request
from starlette.responses import Response

from app.admin.app import create_admin_app
from app.chat.router import router as chat_router
from app.community.bootstrap import ensure_community_mock_data
from app.community.router import router as community_router
from app.config import Settings, get_settings
from app.courses.router import router as courses_router
from app.db import SessionLocal
from app.errors import register_exception_handlers
from app.health import router as health_router
from app.locations.bootstrap import DEFAULT_LOCATION_MANIFEST, ensure_location_data
from app.locations.router import router as locations_router
from app.openapi import install_canonical_openapi

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    *,
    bootstrap_locations: bool = False,
    bootstrap_community: bool = False,
    session_factory: sessionmaker[Session] = SessionLocal,
    location_manifest: str | Path = DEFAULT_LOCATION_MANIFEST,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        del app
        if bootstrap_locations:
            ensure_location_data(session_factory, location_manifest)
        if bootstrap_community:
            ensure_community_mock_data(session_factory)
        yield

    app = FastAPI(title="뭐할구 API", version="1.0.0", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    @app.middleware("http")
    async def log_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "route": getattr(route, "path", request.url.path),
                "status_code": response.status_code,
                "elapsed_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )
        return response

    app.include_router(locations_router)
    app.include_router(courses_router)
    app.include_router(community_router)
    app.include_router(chat_router)
    app.include_router(health_router)
    app.mount("/admin", create_admin_app(resolved_settings))
    install_canonical_openapi(app)
    return app


app = create_app(bootstrap_locations=True, bootstrap_community=True)
