from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat.router import router as chat_router
from app.community.router import router as community_router
from app.config import Settings, get_settings
from app.errors import register_exception_handlers
from app.locations.router import router as locations_router


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
    app.include_router(locations_router)
    app.include_router(community_router)
    app.include_router(chat_router)
    return app


app = create_app()
