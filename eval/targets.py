"""The system-under-test callable LangSmith's `evaluate()` invokes once per
dataset question (research.md §9). Runs the same retrieval+generation
pipeline the live app uses; `version_label` is carried through purely for
tracking/metadata -- this iteration doesn't yet support genuinely distinct
pipeline configurations per version (see plan.md's Deployment Scope). If the
pipeline raises, the exception propagates so LangSmith marks the run as
errored (`run.error`) rather than silently omitting the question (FR-026).
"""

import asyncio
import sys
from collections.abc import Callable
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from src.services import generation_service, retrieval_service  # noqa: E402


def make_target(version_label: str, eval_user_id: str = "eval-harness") -> Callable[[dict], dict]:
    """Returns a sync callable LangSmith's evaluate() can invoke per example."""

    def target(inputs: dict) -> dict:
        question = inputs["question"]

        async def _run() -> tuple:
            question_vector = (await generation_service.embed([question]))[0]
            passages = await retrieval_service.search(
                user_id=eval_user_id, question=question, question_vector=question_vector
            )
            generated, _usage = await generation_service.generate_answer(
                question=question, passages=passages
            )
            return generated, passages

        generated, passages = asyncio.run(_run())

        cited_passage_ids = {c.passage_id for c in generated.citations}
        citations = [
            {"content": p.content, "location_label": p.location_label}
            for p in passages
            if p.id in cited_passage_ids
        ]
        return {
            "answer_text": generated.answer_text,
            "citations": citations,
            "status": generated.status,
            "version": version_label,
        }

    return target
