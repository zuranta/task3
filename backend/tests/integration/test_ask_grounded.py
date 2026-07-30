import pytest


@pytest.mark.asyncio
async def test_upload_then_ask_returns_structured_cited_answer(client, register_user):
    headers, _ = await register_user("grounded1")

    upload = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={
            "file": (
                "company.txt",
                b"Acme Corp was founded in 1994 by Jane Doe in Springfield.",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 202
    document_id = upload.json()["id"]

    response = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "When was Acme Corp founded?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    answer = body["answer"]
    assert answer["status"] == "answered"
    assert answer["answer_text"]
    assert len(answer["citations"]) > 0
    assert answer["citations"][0]["document_id"] == document_id
    assert answer["citations"][0]["source_removed"] is False
    metadata = answer["metadata"]
    assert metadata["prompt_tokens"] > 0
    assert metadata["total_tokens"] == metadata["prompt_tokens"] + metadata["completion_tokens"]
    assert 0 <= metadata["context_window_utilization"] <= 1
