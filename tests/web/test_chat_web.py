from unittest.mock import AsyncMock, MagicMock

import pytest

from app.adapters.web.deps import get_current_web_user
from app.main import app
from app.models.user import User
from app.services.rag_service import RAGService


@pytest.fixture
def mock_rag_service():
    mock = MagicMock(spec=RAGService)
    mock.chat = AsyncMock(return_value="Respondeu com estilo Modern Scriptorium")
    return mock


async def test_get_chat_page(client):
    mock_user = User(full_name="Test Researcher", email="test@example.com")
    app.dependency_overrides[get_current_web_user] = lambda: mock_user

    response = await client.get("/web/chat/1")
    assert response.status_code == 200
    assert "Grifo" in response.text
    assert "Researcher" in response.text
    assert 'id="chat-messages"' in response.text

    app.dependency_overrides.clear()


async def test_post_chat_message_success(client, mock_rag_service):
    from app.adapters.web.routes.chat import get_rag_service

    mock_user = User(full_name="Test Researcher", email="test@example.com")
    app.dependency_overrides[get_current_web_user] = lambda: mock_user
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    response = await client.post(
        "/web/chat/1/message",
        data={"message": "Olá, Grifo!"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "Respondeu com estilo Modern Scriptorium" in response.text
    assert "O Grifo" in response.text or "assistant" in response.text

    app.dependency_overrides.clear()


async def test_thinking_indicator(client):
    response = await client.get("/web/chat/1/thinking")
    assert response.status_code == 200
    assert "consultando os pergaminhos" in response.text
