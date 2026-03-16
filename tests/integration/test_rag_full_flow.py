from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.processing.rag.graph import create_rag_graph
from app.services.rag_service_facade import AgenticRAGController


@pytest.mark.asyncio
async def test_rag_controller_integration():
    """
    Test the full CRAG flow via the controller with mocks.
    """
    # Mock models to avoid 404/API costs
    mock_fast = RunnableLambda(lambda x: AIMessage(content="Mocked internal response"))
    mock_reasoner = RunnableLambda(lambda x: AIMessage(content="Mocked final answer"))

    with (
        patch("app.core.llm.get_fast_model", return_value=mock_fast),
        patch("app.core.llm.get_reasoner", return_value=mock_reasoner),
        patch(
            "app.data_source.vector_store.Chroma.similarity_search",
            return_value=[
                Document(
                    page_content="Company knowledge about Grifo.",
                    metadata={"source": "local"},
                )
            ],
        ),
    ):
        controller = AgenticRAGController()
        question = "Quem é o Strahd von Zarovich?"

        response = await controller.invoke(question)
        assert response is not None
        assert isinstance(response["generation"], str)
        assert len(response) > 0


@pytest.mark.asyncio
async def test_rag_graph_web_search_fallback():
    """
    Specifically tests the flow where web search is triggered.
    """
    # Specifically patch the chains and tools used in the graph nodes
    from app.processing.rag.chains import GradeDocuments

    mock_grader_response = GradeDocuments(binary_score="no")

    mock_reasoner = RunnableLambda(lambda x: AIMessage(content="Mocked generation"))

    with (
        patch("app.processing.rag.nodes.get_retrieval_grader") as mock_get_grader,
        patch(
            "app.processing.rag.nodes.get_rag_generation_chain",
            return_value=mock_reasoner,
        ),
        patch("app.processing.rag.nodes.TavilySearchResults.invoke") as mock_tavily,
    ):
        mock_grader = MagicMock()
        mock_grader.invoke.return_value = mock_grader_response
        mock_get_grader.return_value = mock_grader

        mock_tavily.return_value = [
            Document(page_content="Web result", metadata={"source": "web_search"})
        ]

        app = create_rag_graph()
        question = "Qual a previsão do tempo em Tokyo hoje?"
        inputs = {"question": question}

        result = await app.ainvoke(inputs)

        assert "generation" in result
        assert result["generation"] is not None
        sources = [doc.metadata.get("source") for doc in result.get("documents", [])]
        assert "web_search" in sources or len(result.get("documents", [])) > 0
