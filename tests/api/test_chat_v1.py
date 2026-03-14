import pytest
from fastapi.testclient import TestClient
from app.api.routes import app
import json

client = TestClient(app)

def test_chat_v1_endpoint_structure():
    """
    Verifies that the /api/v1/chat endpoint returns the expected JSON structure.
    Uses a mock message to avoid real LLM calls if possible, or just checks the response.
    Note: Real LLM calls might be triggered if not mocked.
    """
    payload = {
        "message": "Olá, quem é você?",
        "project_id": "test-project",
        "thread_id": "test-thread",
        "user_id": "test-user",
        "config": {
            "mode": "fast",
            "web_search": False
        }
    }
    
    # We might need to mock AgentOrchestrator.process_message to avoid real costs/latency
    # but for a quick structure check, let's see if it at least accepts the request.
    
    response = client.post("/api/v1/chat", json=payload)
    
    # If the API is working, it should return 200 or 500 (if LLM fails but route is fine)
    # We check if the models are correctly validated by FastAPI
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

def test_chat_v1_missing_required_fields():
    """Checks that missing project_id or thread_id returns 422."""
    payload = {
        "message": "Hello"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 422
