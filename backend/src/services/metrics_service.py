"""Operational health metrics from Application Insights, broken down by
request stage (FR-027, FR-028, SC-009, SC-010).

Reuses the `request.stage` custom span the telemetry middleware emits on
every request (src/core/telemetry.py) -- Application Insights is the system
of record; there is no separate metrics table in SQLite (research.md §10).
"""

from datetime import timedelta
from functools import lru_cache

from azure.identity.aio import DefaultAzureCredential
from azure.monitor.query.aio import LogsQueryClient

from src.core.config import get_settings
from src.core.errors import UpstreamServiceError

_KNOWN_STAGES = ("upload", "retrieval", "generation")

# `request.stage` is an INTERNAL-kind span (a child of the auto-instrumented
# FastAPI request span), which the Azure Monitor OpenTelemetry exporter lands
# in the classic `dependencies` table (type "InProc") when queried against
# an Application Insights *resource* ID via query_resource -- distinct from
# the `AppDependencies` table name used when querying a Log Analytics
# *workspace* directly. Confirmed against a live resource: `success` (set
# from the span's OTel status, not from the `http.status_code` attribute --
# that one never actually lands in `customDimensions`) is the reliable
# failure signal; `duration` is already in milliseconds.
_QUERY = """
dependencies
| where name == "request.stage"
| extend stage = tostring(customDimensions["rag.request_stage"])
| extend tokens = toint(customDimensions["rag.total_tokens"])
| summarize
    request_count = count(),
    error_count = countif(success == false),
    p50_latency_ms = percentile(duration, 50),
    p95_latency_ms = percentile(duration, 95),
    total_tokens = sum(tokens)
  by stage
"""


@lru_cache
def _credential() -> DefaultAzureCredential:
    return DefaultAzureCredential()


@lru_cache
def _client() -> LogsQueryClient:
    return LogsQueryClient(_credential())


def _empty_stage() -> dict:
    return {
        "request_count": 0,
        "error_count": 0,
        "error_rate": 0.0,
        "p50_latency_ms": 0.0,
        "p95_latency_ms": 0.0,
        "total_tokens": 0,
    }


async def get_operational_metrics(*, window_minutes: int = 60) -> dict:
    resource_id = get_settings().application_insights_resource_id
    if not resource_id:
        raise UpstreamServiceError("Operational metrics are not configured for this environment.")

    try:
        result = await _client().query_resource(
            resource_id, _QUERY, timespan=timedelta(minutes=window_minutes)
        )
    except Exception as exc:
        raise UpstreamServiceError(
            "Operational metrics could not be retrieved right now. Please try again."
        ) from exc

    by_stage = {stage: _empty_stage() for stage in _KNOWN_STAGES}
    for table in result.tables:
        for row in table.rows:
            request_count = row["request_count"] or 0
            error_count = row["error_count"] or 0
            by_stage[row["stage"]] = {
                "request_count": request_count,
                "error_count": error_count,
                "error_rate": (error_count / request_count) if request_count else 0.0,
                "p50_latency_ms": row["p50_latency_ms"] or 0.0,
                "p95_latency_ms": row["p95_latency_ms"] or 0.0,
                "total_tokens": row["total_tokens"] or 0,
            }

    return {"window_minutes": window_minutes, "by_stage": by_stage}
