import pytest


@pytest.mark.asyncio
async def test_question_with_no_documents_uploaded_returns_no_answer_found(client, register_user):
    headers, _ = await register_user("noanswer1")

    response = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "What is the airspeed of a swallow?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_answer_found"
    assert body["answer"]["answer_text"] is None
    assert body["answer"]["citations"] == []


@pytest.mark.asyncio
async def test_question_unrelated_to_uploaded_content_returns_no_answer_found(
    client, register_user
):
    headers, _ = await register_user("noanswer2")
    await client.post(
        "/api/v1/documents",
        headers=headers,
        files={
            "file": (
                "recipe.txt",
                b"Preheat the oven to three hundred fifty degrees.",
                "text/plain",
            )
        },
    )

    response = await client.post(
        "/api/v1/queries",
        headers=headers,
        json={"question": "What is the boiling point of nitrogen?"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "no_answer_found"
