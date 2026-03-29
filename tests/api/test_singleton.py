from unittest.mock import AsyncMock, patch

import pytest

from app.adapters.api.routers.chat import get_orchestrator, get_vector_store


@pytest.fixture(autouse=True)
def reset_singletons():
    """Garante singletons limpos antes e depois de cada teste."""
    import app.adapters.api.routers.chat as chat_module

    original_orchestrator = chat_module._orchestrator
    original_vector_store = chat_module._vector_store
    chat_module._orchestrator = None
    chat_module._vector_store = None
    yield
    chat_module._orchestrator = original_orchestrator
    chat_module._vector_store = original_vector_store


def test_get_orchestrator_retorna_mesma_instancia():
    """Chamadas consecutivas a get_orchestrator devem retornar a mesma instância."""
    with patch("app.adapters.api.routers.chat.AgentOrchestrator") as mock_cls:
        # instance = mock_cls.return_value
        first = get_orchestrator()
        second = get_orchestrator()

    assert first is second
    mock_cls.assert_called_once()


def test_get_vector_store_retorna_mesma_instancia():
    """Chamadas consecutivas a get_vector_store devem retornar a mesma instância."""
    with patch("app.adapters.api.routers.chat.VectorStoreManager") as mock_cls:
        # instance = mock_cls.return_value
        first = get_vector_store()
        second = get_vector_store()

    assert first is second
    mock_cls.assert_called_once()


async def test_lifespan_inicializa_singletons_no_startup():
    """O lifespan deve criar e inicializar os singletons antes da primeira request."""
    import app.adapters.api.routers.chat as chat_module

    mock_orchestrator = AsyncMock()
    mock_orchestrator._ensure_initialized = AsyncMock()

    with (
        patch(
            "app.adapters.api.routers.chat.AgentOrchestrator",
            return_value=mock_orchestrator,
        ),
        patch("app.adapters.api.routers.chat.VectorStoreManager"),
        patch("app.core.db.engine"),
    ):
        from fastapi import FastAPI

        from app.main import lifespan

        test_app = FastAPI()
        async with lifespan(test_app):
            # Dentro do lifespan: singletons devem estar inicializados
            assert chat_module._orchestrator is not None
            assert chat_module._vector_store is not None
            mock_orchestrator._ensure_initialized.assert_called_once()
