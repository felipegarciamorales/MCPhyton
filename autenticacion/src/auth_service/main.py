from contextlib import asynccontextmanager

from fastapi import FastAPI

from auth_service.infrastructure.persistence.database import init_db
from auth_service.presentation.api.auth_router import router as auth_router
from auth_service.presentation.error_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Auth Service",
        description="JWT-based authentication service built with FastAPI and DDD layering.",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    app.include_router(auth_router)
    return app


app = create_app()
