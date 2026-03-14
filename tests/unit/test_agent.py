import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.memory import InMemoryStore
from langchain_core.tools import tool

from app.processing.agent import AgentOrchestrator
from app.core.config import settings
from app.processing.schemas import KnowledgeExtraction
from app.processing.memory import StoreMemoryManager, VectorizedMessageHistory


@pytest.fixture
def mock_llms():
    """Mock LLMs patches para as chains diretamente."""
    
    TOOL_CALL = {
        "name": "answer_question_tool",
        "args": {"answer": "Mock", "reflection": {}, "search_queries": []},
        "id": "call_abc123",
        "type": "tool"
    }
    
    mock_draft = MagicMock()
    mock_draft.ainvoke = AsyncMock(return_value=AIMessage(
        content="Draft answer", 
        tool_calls=[TOOL_CALL]
    ))
    
    mock_revise = MagicMock()
    reasoner_tool_call = TOOL_CALL.copy()
    reasoner_tool_call["name"] = "revise_answer_tool"
    mock_revise.ainvoke = AsyncMock(return_value=AIMessage(
        content="Revised answer", 
        tool_calls=[reasoner_tool_call]
    ))
    
    mock_extract = MagicMock()
    mock_extract.ainvoke = AsyncMock(return_value=KnowledgeExtraction(facts=[]))
    
    with patch('app.processing.agent.get_first_responder', return_value=mock_draft), \
         patch('app.processing.agent.get_revisor', return_value=mock_revise), \
         patch('app.processing.agent.get_knowledge_extractor', return_value=mock_extract):
        yield mock_draft, mock_revise, mock_extract


@pytest.fixture
def mock_store_manager():
    manager = MagicMock(spec=StoreMemoryManager)
    manager.store = MagicMock()  # Ensure nested store is also mocked
    manager.store.asearch = AsyncMock(return_value=[])
    manager.store.aput = AsyncMock()
    manager.search_memories = AsyncMock(return_value=[])
    manager.save_fact = AsyncMock()
    return manager


@pytest.fixture
def mock_history_db():
    db = MagicMock(spec=VectorizedMessageHistory)
    db.search_history.return_value = ""  # Returns str, not mock
    db.add_message = AsyncMock()
    return db


@pytest.fixture
def mock_settings():
    with patch('app.core.config.settings.REFLEXION_MAX_ITERATIONS', 1):
        yield


class TestAgentOrchestrator:
    """Testes completos."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_llms, mock_store_manager):
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        assert orchestrator.graph is not None
        assert isinstance(orchestrator.reflexion_tools, ToolNode)

    @pytest.mark.asyncio
    async def test_single_iteration(self, mock_llms, mock_store_manager, mock_history_db, mock_settings):
        # Patch class constructors: intercepts instantiation inside AgentOrchestrator
        with patch('app.processing.agent.StoreMemoryManager', return_value=mock_store_manager), \
             patch('app.processing.agent.VectorizedMessageHistory', return_value=mock_history_db):
            
            orchestrator = AgentOrchestrator(store=InMemoryStore())
            
            result = await orchestrator.process_message(
                "Test", "thread1", "proj1", "user1"
            )
            
            assert "response" in result
            assert "usage" in result
            assert result["response"] is not None

    @pytest.mark.asyncio
    async def test_event_loop_terminates(self, mock_llms, mock_store_manager, mock_history_db):
        settings.REFLEXION_MAX_ITERATIONS = 1
        with patch('app.processing.agent.StoreMemoryManager', return_value=mock_store_manager), \
             patch('app.processing.agent.VectorizedMessageHistory', return_value=mock_history_db):
            
            orchestrator = AgentOrchestrator(store=InMemoryStore())
            
            result = await orchestrator.process_message("test", "t1", "p1")
            assert "iterations" in result
            assert result["iterations"] <= 2 # Draft + Revise

    @pytest.mark.asyncio
    async def test_memory_retrieval(self, mock_llms, mock_store_manager, mock_history_db):
        # mock_history_db já é MagicMock com search_history dummy
        mock_history_db.search_history.return_value = "Mock history"
        
        with patch('app.processing.agent.StoreMemoryManager', return_value=mock_store_manager), \
             patch('app.processing.agent.VectorizedMessageHistory', return_value=mock_history_db):
            
            orchestrator = AgentOrchestrator(store=InMemoryStore())
            
            state = {"messages": [HumanMessage(content="test")]}
            config = {"configurable": {"thread_id": "t1", "user_id": "u1", "project_id": "p1"}}
            
            result = await orchestrator.retrieve_memory_node(state, config)
            
            assert len(result["messages"]) == 1
            assert "Relevant Conversation History" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_knowledge_extraction_empty(self, mock_llms, mock_store_manager):
        # Mock extractor retorna lista vazia
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(facts=[])
        
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager
        
        state = {"messages": [AIMessage(content="test")]}
        config = {"configurable": {"user_id": "test-user"}}
        
        await orchestrator.extract_knowledge_node(state, config)
        
        mock_store_manager.save_fact.assert_not_called()

    @pytest.mark.asyncio
    async def test_knowledge_extraction_success(self, mock_llms, mock_store_manager):
        # Mock extractor retorna um fato
        from app.processing.schemas import ExtractedFact
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(
            facts=[ExtractedFact(fact="User likes Python", topic="preferences")]
        )
        
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager
        
        state = {"messages": [
            HumanMessage(content="Eu gosto de Python"),
            AIMessage(content="Que legal!")
        ]}
        config = {"configurable": {"user_id": "test-user"}}
        
        await orchestrator.extract_knowledge_node(state, config)
        
        mock_store_manager.save_fact.assert_called_once()
        args, kwargs = mock_store_manager.save_fact.call_args
        assert args[0] == "test-user"
        assert "User likes Python" in args[2]