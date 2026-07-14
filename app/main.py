import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.chat.router import router as chat_router
from app.community.router import router as community_router
from app.config import Settings, get_settings
from app.errors import register_exception_handlers
from app.health import router as health_router
from app.locations.router import router as locations_router
from app.openapi import install_canonical_openapi

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title="뭐할구 API", version="1.0.0")
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
    app.include_router(community_router)
    app.include_router(chat_router)
    app.include_router(health_router)
    install_canonical_openapi(app)
    return app


app = create_app()
