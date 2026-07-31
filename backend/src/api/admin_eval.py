"""Benchmark dataset management + comparison runs (FR-007, FR-023-FR-026).

Every route here is gated by `require_admin`: regular user accounts get a
403, never access to dataset items or comparison results.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import require_admin
from src.models.db import ComparisonRun as ComparisonRunRow
from src.models.db import User
from src.models.schemas import ComparisonRun, ComparisonRunRequest, DatasetItem, DeleteIdsRequest
from src.services import eval_service

router = APIRouter(prefix="/api/v1/admin/eval", tags=["admin-eval"])


def _to_schema(run: ComparisonRunRow) -> ComparisonRun:
    return ComparisonRun(
        id=run.id,
        version_a_label=run.version_a_label,
        version_b_label=run.version_b_label,
        status=run.status.value,
        aggregate_score_a=run.aggregate_score_a,
        aggregate_score_b=run.aggregate_score_b,
        winner=run.winner.value if run.winner else None,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


@router.post("/dataset-items", response_model=DatasetItem, status_code=status.HTTP_201_CREATED)
async def add_dataset_item(
    body: DatasetItem,
    _admin: Annotated[User, Depends(require_admin)],
) -> DatasetItem:
    return eval_service.add_dataset_item(
        question=body.question,
        expected_answer=body.expected_answer,
        expected_source_reference=body.expected_source_reference,
    )


@router.get("/dataset-items", response_model=list[DatasetItem])
async def list_dataset_items(
    _admin: Annotated[User, Depends(require_admin)],
) -> list[DatasetItem]:
    return eval_service.list_dataset_items()


@router.delete("/dataset-items", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset_items(
    body: DeleteIdsRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    eval_service.delete_dataset_items(body.ids)


@router.post("/comparison-runs", response_model=ComparisonRun, status_code=status.HTTP_202_ACCEPTED)
async def start_comparison_run(
    body: ComparisonRunRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComparisonRun:
    run = await eval_service.start_comparison_run(
        db,
        user_id=admin.id,
        version_a_label=body.version_a_label,
        version_b_label=body.version_b_label,
    )
    return _to_schema(run)


@router.get("/comparison-runs", response_model=list[ComparisonRun])
async def list_comparison_runs(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ComparisonRun]:
    runs = await eval_service.list_comparison_runs(db)
    return [_to_schema(run) for run in runs]


@router.get("/comparison-runs/{run_id}", response_model=ComparisonRun)
async def get_comparison_run(
    run_id: str,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComparisonRun:
    run = await eval_service.get_comparison_run(db, run_id=run_id)
    return _to_schema(run)


@router.delete("/comparison-runs", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comparison_runs(
    body: DeleteIdsRequest,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await eval_service.delete_comparison_runs(db, run_ids=body.ids)
