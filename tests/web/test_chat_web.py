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


@pytest.fixture
def authenticated_client(client):
    """Client com get_current_web_user substituído por um usuário mock."""
    mock_user = User(full_name="Test Researcher", email="test@example.com")
    app.dependency_overrides[get_current_web_user] = lambda: mock_user
    yield client
    app.dependency_overrides.pop(get_current_web_user, None)


@pytest.fixture
def rag_service_override(mock_rag_service):
    """Substitui get_rag_service pelo mock_rag_service durante o teste."""
    from app.adapters.web.routes.chat import get_rag_service

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    yield
    app.dependency_overrides.pop(get_rag_service, None)


async def test_get_chat_page(authenticated_client):
    response = await authenticated_client.get("/web/chat/1")
    assert response.status_code == 200
    assert "Grifo" in response.text
    assert "Researcher" in response.text
    assert 'id="chat-messages"' in response.text


async def test_post_chat_message_success(
    authenticated_client, mock_rag_service, rag_service_override
):
    response = await authenticated_client.post(
        "/web/chat/1/message",
        data={"message": "Olá, Grifo!"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "Respondeu com estilo Modern Scriptorium" in response.text
    assert "O Grifo" in response.text or "assistant" in response.text


async def test_thinking_indicator(client):
    response = await client.get("/web/chat/1/thinking")
    assert response.status_code == 200
    assert "consultando os pergaminhos" in response.text
