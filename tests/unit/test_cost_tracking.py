from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.store.memory import InMemoryStore

from app.processing.agent import _extract_usage_from_messages


def _ai_msg(content="", input_tokens=0, output_tokens=0):
    """Cria AIMessage com usage_metadata válido (total_tokens é obrigatório pelo schema)."""
    return AIMessage(
        content=content,
        usage_metadata={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
    )


def test_extract_usage_soma_tokens_de_ai_messages():
    messages = [
        _ai_msg("a", input_tokens=10, output_tokens=5),
        _ai_msg("b", input_tokens=20, output_tokens=8),
    ]
    result = _extract_usage_from_messages(messages)
    assert result["prompt_tokens"] == 30
    assert result["completion_tokens"] == 13
    assert result["total_tokens"] == 43


def test_extract_usage_ignora_messages_sem_metadata():
    messages = [
        AIMessage(content="sem metadata"),
        _ai_msg("com metadata", input_tokens=5, output_tokens=3),
    ]
    result = _extract_usage_from_messages(messages)
    assert result["prompt_tokens"] == 5
    assert result["completion_tokens"] == 3
    assert result["total_tokens"] == 8


def test_extract_usage_ignora_mensagens_nao_ai():
    messages = [
        HumanMessage(content="user"),
        ToolMessage(content="tool result", tool_call_id="c1"),
        SystemMessage(content="system"),
        _ai_msg("ai", input_tokens=7, output_tokens=2),
    ]
    result = _extract_usage_from_messages(messages)
    assert result["prompt_tokens"] == 7
    assert result["completion_tokens"] == 2


def test_extract_usage_lista_vazia_retorna_zeros():
    result = _extract_usage_from_messages([])
    assert result == {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def test_extract_usage_metadata_none_nao_lanca_excecao():
    messages = [AIMessage(content="ok", usage_metadata=None)]
    result = _extract_usage_from_messages(messages)
    assert result["total_tokens"] == 0


# ── process_message: comportamento por provider ───────────────────────────────


async def test_process_message_openai_usa_openai_callback(
    mock_llms, mock_store_manager, mock_history_db
):
    with (
        patch(
            "app.processing.agent.StoreMemoryManager", return_value=mock_store_manager
        ),
        patch(
            "app.processing.agent.VectorizedMessageHistory",
            return_value=mock_history_db,
        ),
        patch("app.processing.agent.settings") as mock_settings,
    ):
        mock_settings.MODEL_PROVIDER = "openai"
        mock_settings.REFLEXION_MAX_ITERATIONS = 1
        mock_settings.MEMORY_DB_PATH = ":memory:"

        from app.processing.agent import AgentOrchestrator

        orchestrator = AgentOrchestrator(store=InMemoryStore())

        result = await orchestrator.process_message("Test", "t1", "p1", "u1")

        assert "usage" in result
        assert "total_cost" in result["usage"]
        # OpenAI callback retorna float (pode ser 0.0 com mocks, mas nunca None)
        assert result["usage"]["total_cost"] is not None


async def test_process_message_deepseek_total_cost_null(
    mock_llms, mock_store_manager, mock_history_db
):
    with (
        patch(
            "app.processing.agent.StoreMemoryManager", return_value=mock_store_manager
        ),
        patch(
            "app.processing.agent.VectorizedMessageHistory",
            return_value=mock_history_db,
        ),
        patch("app.processing.agent.settings") as mock_settings,
    ):
        mock_settings.MODEL_PROVIDER = "deepseek"
        mock_settings.REFLEXION_MAX_ITERATIONS = 1
        mock_settings.MEMORY_DB_PATH = ":memory:"

        from app.processing.agent import AgentOrchestrator

        orchestrator = AgentOrchestrator(store=InMemoryStore())

        result = await orchestrator.process_message("Test", "t1", "p1", "u1")

        assert result["usage"]["total_cost"] is None


@pytest.mark.parametrize("provider", ["deepseek", "anthropic", "google"])
async def test_process_message_providers_sem_custo_retornam_total_cost_null(
    provider, mock_llms, mock_store_manager, mock_history_db
):
    with (
        patch(
            "app.processing.agent.StoreMemoryManager", return_value=mock_store_manager
        ),
        patch(
            "app.processing.agent.VectorizedMessageHistory",
            return_value=mock_history_db,
        ),
        patch("app.processing.agent.settings") as mock_settings,
    ):
        mock_settings.MODEL_PROVIDER = provider
        mock_settings.REFLEXION_MAX_ITERATIONS = 1
        mock_settings.MEMORY_DB_PATH = ":memory:"

        from app.processing.agent import AgentOrchestrator

        orchestrator = AgentOrchestrator(store=InMemoryStore())

        result = await orchestrator.process_message("Test", "t1", "p1", "u1")

        assert result["usage"]["total_cost"] is None, (
            f"Provider '{provider}' deve retornar total_cost=None, não zeros enganosos."
        )


async def test_process_message_provider_sem_custo_loga_warning(
    mock_llms, mock_store_manager, mock_history_db, caplog
):
    import logging

    with (
        patch(
            "app.processing.agent.StoreMemoryManager", return_value=mock_store_manager
        ),
        patch(
            "app.processing.agent.VectorizedMessageHistory",
            return_value=mock_history_db,
        ),
        patch("app.processing.agent.settings") as mock_settings,
    ):
        mock_settings.MODEL_PROVIDER = "deepseek"
        mock_settings.REFLEXION_MAX_ITERATIONS = 1
        mock_settings.MEMORY_DB_PATH = ":memory:"

        from app.processing.agent import AgentOrchestrator

        orchestrator = AgentOrchestrator(store=InMemoryStore())

        with caplog.at_level(logging.WARNING):
            await orchestrator.process_message("Test", "t1", "p1", "u1")

        assert any(
            "cost tracking" in r.message.lower() or "total_cost" in r.message.lower()
            for r in caplog.records
        ), "Deve logar um warning quando o provider não suporta cost tracking."
