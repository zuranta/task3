"""metrics_service aggregates mixed success/failure traffic into per-stage
operational metrics, and honors the requested time window so data is never
more than the requested staleness bound old (FR-027, FR-028, SC-009, SC-010).

The Application Insights query client is faked at the boundary metrics_service
calls it through (mirrors eval_service's LangSmith Client mocking) -- this
validates the aggregation/parsing logic, not a live Log Analytics query.
"""

from datetime import timedelta

import pytest

from src.services import metrics_service


class _FakeSettings:
    application_insights_resource_id = (
        "/subscriptions/x/resourceGroups/y/providers/Microsoft.Insights/components/z"
    )


class _FakeTable:
    def __init__(self, rows):
        self.rows = rows


class _FakeResult:
    def __init__(self, rows):
        self.tables = [_FakeTable(rows)]


class _FakeLogsQueryClient:
    def __init__(self, rows):
        self._rows = rows
        self.calls: list[dict] = []

    async def query_resource(self, resource_id, query, *, timespan):
        self.calls.append({"resource_id": resource_id, "query": query, "timespan": timespan})
        return _FakeResult(self._rows)


@pytest.fixture(autouse=True)
def _fake_metrics_settings(monkeypatch):
    monkeypatch.setattr(metrics_service, "get_settings", lambda: _FakeSettings())


@pytest.mark.asyncio
async def test_mixed_success_and_failure_traffic_is_reflected_per_stage(monkeypatch):
    # 10 upload requests, 1 failed; 8 retrieval, all succeeded; 8 generation, 2 failed.
    rows = [
        {
            "stage": "upload",
            "request_count": 10,
            "error_count": 1,
            "p50_latency_ms": 120.0,
            "p95_latency_ms": 300.0,
            "total_tokens": 0,
        },
        {
            "stage": "retrieval",
            "request_count": 8,
            "error_count": 0,
            "p50_latency_ms": 80.0,
            "p95_latency_ms": 150.0,
            "total_tokens": 0,
        },
        {
            "stage": "generation",
            "request_count": 8,
            "error_count": 2,
            "p50_latency_ms": 900.0,
            "p95_latency_ms": 2000.0,
            "total_tokens": 4200,
        },
    ]
    fake_client = _FakeLogsQueryClient(rows)
    monkeypatch.setattr(metrics_service, "_client", lambda: fake_client)

    result = await metrics_service.get_operational_metrics(window_minutes=60)

    assert result["window_minutes"] == 60
    assert result["by_stage"]["upload"]["request_count"] == 10
    assert result["by_stage"]["upload"]["error_count"] == 1
    assert result["by_stage"]["upload"]["error_rate"] == pytest.approx(0.1)
    assert result["by_stage"]["retrieval"]["error_rate"] == 0.0
    assert result["by_stage"]["generation"]["error_rate"] == pytest.approx(0.25)
    assert result["by_stage"]["generation"]["total_tokens"] == 4200


@pytest.mark.asyncio
async def test_a_stage_with_no_traffic_still_appears_with_zero_counts(monkeypatch):
    fake_client = _FakeLogsQueryClient(rows=[])
    monkeypatch.setattr(metrics_service, "_client", lambda: fake_client)

    result = await metrics_service.get_operational_metrics(window_minutes=60)

    for stage in ("upload", "retrieval", "generation"):
        assert result["by_stage"][stage]["request_count"] == 0
        assert result["by_stage"][stage]["error_rate"] == 0.0


@pytest.mark.asyncio
async def test_requested_window_bounds_how_stale_the_data_can_be(monkeypatch):
    """SC-009/SC-010: data must never be staler than the requested window --
    verified by checking the actual timespan passed to the query client."""
    fake_client = _FakeLogsQueryClient(rows=[])
    monkeypatch.setattr(metrics_service, "_client", lambda: fake_client)

    await metrics_service.get_operational_metrics(window_minutes=5)

    assert fake_client.calls[0]["timespan"] == timedelta(minutes=5)


@pytest.mark.asyncio
async def test_metrics_unavailable_when_application_insights_is_not_configured(monkeypatch):
    class _Unconfigured:
        application_insights_resource_id = None

    monkeypatch.setattr(metrics_service, "get_settings", lambda: _Unconfigured())

    from src.core.errors import UpstreamServiceError

    with pytest.raises(UpstreamServiceError):
        await metrics_service.get_operational_metrics(window_minutes=60)
