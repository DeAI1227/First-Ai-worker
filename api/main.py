from __future__ import annotations

from project_env import load_project_env

load_project_env()

from fastapi import FastAPI

from api.config import load_api_settings
from api.routes.collect import router as collect_router
from api.routes.health import router as health_router
from api.routes.ingestion import router as ingestion_router
from api.routes.pipeline import router as pipeline_router
from api.routes.promotion import router as promotion_router


def create_app() -> FastAPI:
    settings = load_api_settings()
    app = FastAPI(title="investment_research_collector", version="mvp")
    app.state.api_auth_token = settings.api_auth_token
    app.state.service_name = settings.service_name
    app.state.service_version = settings.version
    app.include_router(health_router)
    app.include_router(collect_router)
    app.include_router(ingestion_router)
    app.include_router(promotion_router)
    app.include_router(pipeline_router)
    return app


app = create_app()
