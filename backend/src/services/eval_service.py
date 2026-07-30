"""Benchmark dataset management + comparison-run orchestration (US4,
FR-022-FR-026).

Dataset items live in LangSmith (data-model.md's Evaluation Dataset Item,
not duplicated in SQLite); comparison-run summaries are persisted here as
ComparisonRun rows so the admin UI can list past runs without querying
LangSmith directly each time.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError, UpstreamServiceError
from src.models import schemas
from src.models.db import ComparisonRun, ComparisonRunStatus, ComparisonWinner

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eval import dataset_sync  # noqa: E402
from eval.run_experiment import run_experiment  # noqa: E402


def add_dataset_item(
    *, question: str, expected_answer: str, expected_source_reference: str | None = None
) -> schemas.DatasetItem:
    item = dataset_sync.add_dataset_item(
        question=question,
        expected_answer=expected_answer,
        expected_source_reference=expected_source_reference,
    )
    return schemas.DatasetItem(**item)


def list_dataset_items() -> list[schemas.DatasetItem]:
    return [schemas.DatasetItem(**item) for item in dataset_sync.list_dataset_items()]


async def start_comparison_run(
    db: AsyncSession, *, user_id: str, version_a_label: str, version_b_label: str
) -> ComparisonRun:
    run = ComparisonRun(
        version_a_label=version_a_label,
        version_b_label=version_b_label,
        status=ComparisonRunStatus.running,
        created_by=user_id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    try:
        result = run_experiment(version_a_label=version_a_label, version_b_label=version_b_label)
    except Exception as exc:
        run.status = ComparisonRunStatus.partial
        run.completed_at = datetime.now(UTC)
        await db.commit()
        raise UpstreamServiceError(
            "The comparison run could not be completed right now. Please try again."
        ) from exc

    run.langsmith_experiment_id_a = result["langsmith_experiment_id_a"]
    run.langsmith_experiment_id_b = result["langsmith_experiment_id_b"]
    run.aggregate_score_a = result["aggregate_score_a"]
    run.aggregate_score_b = result["aggregate_score_b"]
    run.winner = ComparisonWinner(result["winner"])
    run.status = (
        ComparisonRunStatus.partial if result["had_failures"] else ComparisonRunStatus.completed
    )
    run.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(run)
    return run


async def list_comparison_runs(db: AsyncSession) -> list[ComparisonRun]:
    result = await db.execute(select(ComparisonRun).order_by(ComparisonRun.started_at.desc()))
    return list(result.scalars().all())


async def get_comparison_run(db: AsyncSession, *, run_id: str) -> ComparisonRun:
    result = await db.execute(select(ComparisonRun).where(ComparisonRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Comparison run not found.")
    return run
