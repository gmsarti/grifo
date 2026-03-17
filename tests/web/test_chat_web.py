from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.adapters.web.routes.chat import get_rag_service
from app.main import app
from app.services.rag_service import RAGService

client = TestClient(app)


@pytest.fixture
def mock_rag_service():
    mock = MagicMock(spec=RAGService)
    mock.chat = AsyncMock(return_value="Respondeu com estilo Modern Scriptorium")
    return mock


def test_get_chat_page(mocker):
    # Mocking high level dependencies if needed, but here we just want to see if it renders
    # To test the page, we might need a session in the DB or mock the repository.
    # For now, let's test if the route exists and returns 200 with basic HTML.

    # Mock the database session and repo in the dependency override if necessary
    # but a simpler approach for now is checking the template content.
    response = client.get("/web/chat/1")
    assert response.status_code == 200
    assert "Grifo" in response.text
    assert "Modern Scriptorium" in response.text
    assert 'id="chat-messages"' in response.text


def test_post_chat_message_success(mock_rag_service):
    # Override the dependency
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    response = client.post(
        "/web/chat/1/message",
        data={"message": "Olá, Grifo!"},
        headers={"HX-Request": "true"},  # Emulate HTMX request
    )

    assert response.status_code == 200
    assert "Respondeu com estilo Modern Scriptorium" in response.text
    assert "staggered-reveal" in response.text
    assert "O Grifo" in response.text

    # Cleanup overrides
    app.dependency_overrides.clear()


def test_thinking_indicator():
    response = client.get("/web/chat/1/thinking")
    assert response.status_code == 200
    assert "consultando os pergaminhos" in response.text
