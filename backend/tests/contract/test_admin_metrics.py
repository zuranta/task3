"""GET /admin/metrics (admin/evaluator only, FR-027, FR-028)."""

import pytest

from src.services import metrics_service


@pytest.mark.asyncio
async def test_non_admin_cannot_view_metrics(client, register_user):
    headers, _ = await register_user("regularmetrics1")

    response = await client.get("/api/v1/admin/metrics", headers=headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_caller_cannot_view_metrics(client):
    response = await client.get("/api/v1/admin/metrics")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_sees_metrics_with_per_stage_breakdown(client, register_admin, monkeypatch):
    fake_metrics = {
        "window_minutes": 60,
        "by_stage": {
            "upload": {
                "request_count": 10,
                "error_count": 1,
                "error_rate": 0.1,
                "p50_latency_ms": 120.0,
                "p95_latency_ms": 300.0,
                "total_tokens": 0,
            },
            "retrieval": {
                "request_count": 8,
                "error_count": 0,
                "error_rate": 0.0,
                "p50_latency_ms": 80.0,
                "p95_latency_ms": 150.0,
                "total_tokens": 0,
            },
            "generation": {
                "request_count": 8,
                "error_count": 2,
                "error_rate": 0.25,
                "p50_latency_ms": 900.0,
                "p95_latency_ms": 2000.0,
                "total_tokens": 4200,
            },
        },
    }

    async def fake_get_operational_metrics(*, window_minutes=60):
        assert window_minutes == 60
        return fake_metrics

    monkeypatch.setattr(metrics_service, "get_operational_metrics", fake_get_operational_metrics)

    headers, _ = await register_admin("metricsadmin1")

    response = await client.get("/api/v1/admin/metrics", headers=headers)

    assert response.status_code == 200
    assert response.json() == fake_metrics


@pytest.mark.asyncio
async def test_admin_can_request_a_custom_window(client, register_admin, monkeypatch):
    captured = {}

    async def fake_get_operational_metrics(*, window_minutes=60):
        captured["window_minutes"] = window_minutes
        return {"window_minutes": window_minutes, "by_stage": {}}

    monkeypatch.setattr(metrics_service, "get_operational_metrics", fake_get_operational_metrics)

    headers, _ = await register_admin("metricsadmin2")

    response = await client.get("/api/v1/admin/metrics?window_minutes=15", headers=headers)

    assert response.status_code == 200
    assert captured["window_minutes"] == 15
    assert response.json()["window_minutes"] == 15


@pytest.mark.asyncio
async def test_window_minutes_must_be_positive(client, register_admin):
    headers, _ = await register_admin("metricsadmin3")

    response = await client.get("/api/v1/admin/metrics?window_minutes=0", headers=headers)

    assert response.status_code == 422
