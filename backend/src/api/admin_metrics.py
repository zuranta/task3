"""Operational health metrics (FR-027, FR-028).

Gated by `require_admin`: regular user accounts get a 403, never access to
production latency/token/error-rate figures.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam

from src.core.security import require_admin
from src.models.db import User
from src.models.schemas import OperationalMetrics
from src.services import metrics_service

router = APIRouter(prefix="/api/v1/admin/metrics", tags=["admin-metrics"])


@router.get("", response_model=OperationalMetrics)
async def get_operational_metrics(
    _admin: Annotated[User, Depends(require_admin)],
    window_minutes: Annotated[int, QueryParam(ge=1, le=1440)] = 60,
) -> OperationalMetrics:
    metrics = await metrics_service.get_operational_metrics(window_minutes=window_minutes)
    return OperationalMetrics(**metrics)
