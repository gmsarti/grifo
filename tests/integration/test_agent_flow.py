import pytest
import asyncio
from app.processing.agent import AgentOrchestrator
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_agent_orchestrator_initialization():
    orchestrator = AgentOrchestrator()
    assert orchestrator.graph is not None
    assert orchestrator.first_responder is not None
    assert orchestrator.revisor is not None

@pytest.mark.asyncio
async def test_agent_process_message_mocked():
    orchestrator = AgentOrchestrator()
    
    # Mock the graph execution to avoid real LLM calls in this test
    # but we will check the structure
    with patch.object(orchestrator.graph, "ainvoke", new_callable=AsyncMock) as mock_invoke:
        from langchain_core.messages import AIMessage
        mock_invoke.return_value = {
            "messages": [
                AIMessage(content="Final response content")
            ]
        }
        
        response = await orchestrator.process_message("What is the company policy?", thread_id="test_thread")
        
        assert response == "Final response content"
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        assert kwargs["config"]["configurable"]["thread_id"] == "test_thread"
        assert "What is the company policy?" in str(args[0]["messages"][0].content)

@pytest.mark.asyncio
async def test_tool_executor_crag_flow():
    # This test verifies the logic in tool_executor's run_queries
    from app.processing.tool_executor import run_queries
    
    with patch("app.processing.tool_executor.vector_db") as mock_vdb, \
         patch("app.processing.tool_executor.tavily_tool") as mock_tavily, \
         patch("app.processing.tool_executor.grader_llm") as mock_grader:
        
        # Scenario: Local search returns irrelevant docs -> Fallback to Tavily
        mock_vdb.search_hybrid.return_value = [MagicMock(page_content="Some irrelevant local doc")]
        mock_grader.ainvoke = AsyncMock(return_value=MagicMock(content="NO"))
        mock_tavily.ainvoke = AsyncMock(return_value="Web result content")
        
        result = await run_queries(["test query"])
        
        assert "Web result content" in result
        mock_vdb.search_hybrid.assert_called_with("test query", k=3)
        mock_tavily.ainvoke.assert_called_once()
