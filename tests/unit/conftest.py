from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.processing.memory import StoreMemoryManager
from app.processing.router_chain import RouterDecision
from app.schemas.agent_schemas import KnowledgeExtraction


@pytest.fixture
def mock_llms():
    """
    Patches das factories de chains no agent.py com mocks.
    Inclui get_router_chain para evitar que AgentOrchestrator tente
    instanciar um LLM real ao ser criado nos testes unitários.
    """
    TOOL_CALL = {
        "name": "answer_question_tool",
        "args": {"answer": "Mock", "reflection": {}, "search_queries": []},
        "id": "call_abc123",
        "type": "tool",
    }

    mock_draft = MagicMock()
    mock_draft.ainvoke = AsyncMock(
        return_value=AIMessage(content="Draft answer", tool_calls=[TOOL_CALL])
    )

    mock_revise = MagicMock()
    reasoner_tool_call = {**TOOL_CALL, "name": "revise_answer_tool"}
    mock_revise.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="Revised answer", tool_calls=[reasoner_tool_call]
        )
    )

    mock_extract = MagicMock()
    mock_extract.ainvoke = AsyncMock(return_value=KnowledgeExtraction(facts=[]))

    # Router com comportamento padrão (reflexion) — evita chamar LLM real
    mock_router = MagicMock()
    mock_router.ainvoke = AsyncMock(
        return_value=RouterDecision(intent="reflexion", zona=None, mobiliario=[])
    )

    with (
        patch("app.processing.agent.get_first_responder", return_value=mock_draft),
        patch("app.processing.agent.get_revisor", return_value=mock_revise),
        patch(
            "app.processing.agent.get_knowledge_extractor", return_value=mock_extract
        ),
        patch("app.processing.agent.get_router_chain", return_value=mock_router),
    ):
        yield mock_draft, mock_revise, mock_extract


@pytest.fixture
def mock_router_chain():
    """
    Mock isolado do router_chain para testes que precisam controlar
    a decisão de roteamento (intent, zona, mobiliario).

    Valor padrão: intent="reflexion". Ajuste via mock.ainvoke.return_value
    no corpo do teste quando necessário.
    """
    mock_router = MagicMock()
    mock_router.ainvoke = AsyncMock(
        return_value=RouterDecision(intent="reflexion", zona=None, mobiliario=[])
    )
    with patch("app.processing.agent.get_router_chain", return_value=mock_router):
        yield mock_router


@pytest.fixture
def mock_store_manager():
    manager = MagicMock(spec=StoreMemoryManager)
    manager.store = MagicMock()
    manager.store.asearch = AsyncMock(return_value=[])
    manager.store.aput = AsyncMock()
    manager.search_memories = AsyncMock(return_value=[])
    manager.save_fact = AsyncMock()
    return manager
