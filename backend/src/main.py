"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.admin_eval import router as admin_eval_router
from src.api.auth import router as auth_router
from src.api.documents import router as documents_router
from src.api.queries import router as queries_router
from src.core.config import get_settings
from src.core.errors import register_exception_handlers
from src.core.telemetry import configure_telemetry


def create_app() -> FastAPI:
    app = FastAPI(title="RAG Document Q&A Application", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    configure_telemetry(app, get_settings().applicationinsights_connection_string)

    app.include_router(auth_router)
    app.include_router(documents_router)
    app.include_router(queries_router)
    app.include_router(admin_eval_router)

    # Remaining routers are registered incrementally per user story:
    #   User Story 5: admin_metrics router

    return app


app = create_app()
