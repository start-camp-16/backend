from fastapi import FastAPI

from app.admin.auth import register_admin_exception_handler
from app.admin.router import router
from app.config import Settings
from app.errors import register_exception_handlers


def create_admin_app(settings: Settings) -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.state.settings = settings
    register_exception_handlers(app)
    register_admin_exception_handler(app)
    app.include_router(router)
    return app
