"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    # Routers are registered incrementally per user story:
    #   User Story 1: auth router
    #   User Story 2: documents, queries routers
    #   User Story 3: extends the queries router
    #   User Story 4: admin_eval router
    #   User Story 5: admin_metrics router

    return app


app = create_app()
