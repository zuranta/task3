"""POST/GET /admin/eval/dataset-items (admin/evaluator only, FR-023)."""

import pytest

from src.services import eval_service


@pytest.mark.asyncio
async def test_admin_can_add_and_list_dataset_items(client, register_admin, monkeypatch):
    added: list[dict] = []

    def fake_add(*, question, expected_answer, expected_source_reference=None):
        item = {
            "id": f"item-{len(added)}",
            "question": question,
            "expected_answer": expected_answer,
            "expected_source_reference": expected_source_reference,
        }
        added.append(item)
        return item

    def fake_list():
        return list(added)

    monkeypatch.setattr(eval_service.dataset_sync, "add_dataset_item", fake_add)
    monkeypatch.setattr(eval_service.dataset_sync, "list_dataset_items", fake_list)

    headers, _ = await register_admin("evaladmin1")

    add_response = await client.post(
        "/api/v1/admin/eval/dataset-items",
        headers=headers,
        json={"question": "What is X?", "expected_answer": "X is Y."},
    )
    assert add_response.status_code == 201
    assert add_response.json() == {
        "id": "item-0",
        "question": "What is X?",
        "expected_answer": "X is Y.",
        "expected_source_reference": None,
    }

    list_response = await client.get("/api/v1/admin/eval/dataset-items", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["question"] == "What is X?"


@pytest.mark.asyncio
async def test_admin_can_delete_dataset_items(client, register_admin, monkeypatch):
    deleted_ids: list[str] = []

    def fake_delete(item_ids):
        deleted_ids.extend(item_ids)

    monkeypatch.setattr(eval_service.dataset_sync, "delete_dataset_items", fake_delete)

    headers, _ = await register_admin("evaladmin3")

    response = await client.request(
        "DELETE",
        "/api/v1/admin/eval/dataset-items",
        headers=headers,
        json={"ids": ["item-0", "item-1"]},
    )

    assert response.status_code == 204
    assert deleted_ids == ["item-0", "item-1"]


@pytest.mark.asyncio
async def test_delete_dataset_items_requires_at_least_one_id(client, register_admin):
    headers, _ = await register_admin("evaladmin4")

    response = await client.request(
        "DELETE", "/api/v1/admin/eval/dataset-items", headers=headers, json={"ids": []}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_dataset_item_missing_fields_returns_422(client, register_admin):
    headers, _ = await register_admin("evaladmin2")

    response = await client.post(
        "/api/v1/admin/eval/dataset-items", headers=headers, json={"question": "only a question"}
    )

    assert response.status_code == 422
