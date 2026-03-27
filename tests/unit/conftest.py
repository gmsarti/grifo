from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.processing.memory import StoreMemoryManager
from app.schemas.agent_schemas import KnowledgeExtraction


@pytest.fixture
def mock_llms():
    """Patches get_first_responder, get_revisor e get_knowledge_extractor com mocks."""
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

    with (
        patch("app.processing.agent.get_first_responder", return_value=mock_draft),
        patch("app.processing.agent.get_revisor", return_value=mock_revise),
        patch(
            "app.processing.agent.get_knowledge_extractor", return_value=mock_extract
        ),
    ):
        yield mock_draft, mock_revise, mock_extract


@pytest.fixture
def mock_store_manager():
    manager = MagicMock(spec=StoreMemoryManager)
    manager.store = MagicMock()
    manager.store.asearch = AsyncMock(return_value=[])
    manager.store.aput = AsyncMock()
    manager.search_memories = AsyncMock(return_value=[])
    manager.save_fact = AsyncMock()
    return manager
