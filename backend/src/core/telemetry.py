"""Application Insights / OpenTelemetry bootstrap.

Auto-instruments the FastAPI app and tags every request with the pipeline
stage it belongs to (upload / retrieval / generation / other), so latency,
token usage, and error rate can later be queried per-stage in Application
Insights (FR-027, FR-028).
"""

import logging

from fastapi import FastAPI, Request

logger = logging.getLogger("rag_document_qa")

_STAGE_BY_PATH_PREFIX = {
    "/api/v1/documents": "upload",
    "/api/v1/queries": "generation",
}


def _stage_for_path(path: str) -> str:
    for prefix, stage in _STAGE_BY_PATH_PREFIX.items():
        if path.startswith(prefix):
            return stage
    return "other"


def configure_telemetry(app: FastAPI, connection_string: str | None) -> None:
    if connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=connection_string)
        logger.info("Application Insights telemetry configured.")
    else:
        logger.warning(
            "APPLICATIONINSIGHTS_CONNECTION_STRING not set; running without telemetry export."
        )

    from opentelemetry import trace

    tracer = trace.get_tracer(__name__)

    @app.middleware("http")
    async def stage_tagging_middleware(request: Request, call_next):
        stage = _stage_for_path(request.url.path)
        with tracer.start_as_current_span("request.stage") as span:
            span.set_attribute("rag.request_stage", stage)
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            return response
