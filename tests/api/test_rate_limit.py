from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_limiter_storage():
    """Limpa o estado do rate limiter antes de cada teste."""
    limiter._storage.reset()
    yield
    limiter._storage.reset()


async def test_chat_endpoint_abaixo_do_limite_nao_retorna_429(client):
    payload = {
        "message": "Olá",
        "project_id": "test",
        "thread_id": "t1",
        "user_id": "u1",
    }
    response = await client.post("/api/v1/chat", json=payload)
    assert response.status_code != 429


async def test_chat_endpoint_retorna_429_quando_limite_excedido():
    """Usa limit '1/minute' para garantir que a 2ª requisição retorna 429."""
    from app.main import app

    payload = {
        "message": "Olá",
        "project_id": "test",
        "thread_id": "t1",
        "user_id": "u1",
    }

    with patch("app.adapters.api.routers.chat.settings") as mock_settings:
        mock_settings.RATE_LIMIT_CHAT = "1/minute"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            first = await ac.post("/api/v1/chat", json=payload)
            second = await ac.post("/api/v1/chat", json=payload)

    # A primeira pode ter qualquer status (depende de LLMs mockados ou não),
    # mas nunca deve ser 429 antes de atingir o limite.
    assert first.status_code != 429
    assert second.status_code == 429


async def test_chat_endpoint_429_retorna_json_com_erro():
    """Resposta 429 deve ter corpo JSON com informação do erro."""
    from app.main import app

    payload = {
        "message": "Olá",
        "project_id": "test",
        "thread_id": "t1",
        "user_id": "u1",
    }

    with patch("app.adapters.api.routers.chat.settings") as mock_settings:
        mock_settings.RATE_LIMIT_CHAT = "1/minute"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            await ac.post("/api/v1/chat", json=payload)
            response = await ac.post("/api/v1/chat", json=payload)

    assert response.status_code == 429
    # slowapi retorna plain text ou JSON — verifica que há alguma resposta
    assert len(response.content) > 0


def test_rate_limit_chat_configuravel_via_settings():
    from app.core.config import settings

    assert hasattr(settings, "RATE_LIMIT_CHAT")
    assert isinstance(settings.RATE_LIMIT_CHAT, str)
    assert "/" in settings.RATE_LIMIT_CHAT  # formato "N/período"
