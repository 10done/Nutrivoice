from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.meals import router as meals_router
from app.api.users import router as users_router
from app.config import get_settings
from app.db import init_db

WEB_ROOT = Path(__file__).resolve().parent.parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(meals_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    if WEB_ROOT.is_dir():
        app.mount("/", StaticFiles(directory=str(WEB_ROOT), html=True), name="web")

    return app


app = create_app()
