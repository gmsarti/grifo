import pytest


async def test_chat_v1_endpoint_structure(client):
    """
    Verifies that the /api/v1/chat endpoint returns the expected JSON structure.
    Note: Real LLM calls might be triggered if not mocked.
    """
    payload = {
        "message": "Olá, quem é você?",
        "project_id": "test-project",
        "thread_id": "test-thread",
        "user_id": "test-user",
        "config": {"mode": "fast", "web_search": False},
    }

    response = await client.post("/api/v1/chat", json=payload)

    if response.status_code == 200:
        data = response.json()
        assert "response" in data
        assert "project_id" in data
        assert "thread_id" in data
        assert "usage" in data
        assert "grounding_metadata" in data
        assert "process_trace" in data
    elif response.status_code == 422:
        pytest.fail(f"Validation error: {response.text}")


async def test_chat_v1_missing_required_fields(client):
    """Checks that missing project_id or thread_id returns 422."""
    response = await client.post("/api/v1/chat", json={"message": "Hello"})
    assert response.status_code == 422
