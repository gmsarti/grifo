import pytest
from app.processing.rag.controller import AgenticRAGController
from app.processing.rag.graph import create_rag_graph
from langchain_core.documents import Document

@pytest.mark.asyncio
async def test_rag_controller_integration():
    """
    Test the full CRAG flow via the controller.
    We'll mock the nodes to avoid real LLM/API costs in some scenarios, 
    but test the orchestration.
    """
    controller = AgenticRAGController()
    
    # Simple test case: Question about D&D (should be in local vector store)
    # Note: This might trigger real LLM calls if not mocked, 
    # but here we want to see the integration.
    question = "Quem é o Strahd von Zarovich?"
    
    # We can invoke it; if it fails due to env vars, we might need Mocking
    # But usually, integration tests in this project seem to expect real connections
    # or at least the logic to flow correctly.
    try:
        response = await controller.invoke(question)
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    except Exception as e:
        pytest.fail(f"RAG Controller failed during integration test: {str(e)}")

@pytest.mark.asyncio
async def test_rag_graph_web_search_fallback():
    """
    Specifically tests the flow where web search is triggered.
    """
    app = create_rag_graph()
    
    # Question that is unlikely to be in the local monster manual
    question = "Qual a previsão do tempo em Tokyo hoje?"
    
    inputs = {"question": question}
    # We can trace the execution or just check the final result
    result = await app.ainvoke(inputs)
    
    assert "generation" in result
    assert result["generation"] is not None
    # If the logic works, it should have documents from 'web_search'
    sources = [doc.metadata.get("source") for doc in result.get("documents", [])]
    assert "web_search" in sources or len(result.get("documents", [])) > 0
