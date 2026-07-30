"""Pushes admin-curated dataset items into the LangSmith benchmark dataset
(research.md §9, FR-023) -- LangSmith is the system of record for Evaluation
Dataset Items; they are not duplicated in SQLite.
"""

from functools import lru_cache

from langsmith import Client

_DATASET_NAME = "rag-document-qa-benchmark"


@lru_cache
def _client() -> Client:
    return Client()


def ensure_dataset() -> None:
    client = _client()
    if not client.has_dataset(dataset_name=_DATASET_NAME):
        client.create_dataset(dataset_name=_DATASET_NAME)


def add_dataset_item(
    *, question: str, expected_answer: str, expected_source_reference: str | None = None
) -> dict:
    ensure_dataset()
    _client().create_example(
        inputs={"question": question},
        outputs={
            "expected_answer": expected_answer,
            "expected_source_reference": expected_source_reference,
        },
        dataset_name=_DATASET_NAME,
    )
    return {
        "question": question,
        "expected_answer": expected_answer,
        "expected_source_reference": expected_source_reference,
    }


def list_dataset_items() -> list[dict]:
    ensure_dataset()
    items = []
    for example in _client().list_examples(dataset_name=_DATASET_NAME):
        outputs = example.outputs or {}
        items.append(
            {
                "question": example.inputs.get("question", ""),
                "expected_answer": outputs.get("expected_answer", ""),
                "expected_source_reference": outputs.get("expected_source_reference"),
            }
        )
    return items


if __name__ == "__main__":
    ensure_dataset()
    print(f"Dataset '{_DATASET_NAME}' is ready. {len(list_dataset_items())} item(s) so far.")
