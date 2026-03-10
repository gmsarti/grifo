import pytest
from unittest.mock import patch, MagicMock
from app.data_source.vector_store import VectorStoreManager
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


@pytest.fixture
def vector_manager():
    with (
        patch("app.data_source.vector_store.Chroma"),
        patch("app.data_source.vector_store.OpenAIEmbeddings"),
    ):
        vm = VectorStoreManager()
        return vm


def test_hybrid_retrieval(vector_manager):
    docs = [
        Document(page_content="O gato está no telhado", metadata={"id": 1}),
        Document(page_content="O cachorro está no jardim", metadata={"id": 2}),
        Document(page_content="A maçã é vermelha", metadata={"id": 3}),
    ]

    # Mocking the retriever behavior for Chroma
    mock_retriever = MagicMock(spec=BaseRetriever)
    vector_manager.vector_store.as_retriever.return_value = mock_retriever

    # Adicionando documentos (isso inicializa o BM25 e o Ensemble)
    vector_manager.add_documents(docs)

    assert vector_manager.hybrid_retriever is not None

    assert vector_manager.hybrid_retriever is not None

    # Mocking the sub-retrievers to return specific documents
    # Using simple MagicMocks to avoid Pydantic attribute interception
    mock_vec = MagicMock()
    mock_vec.invoke.return_value = [docs[0]]
    mock_bm25 = MagicMock()
    mock_bm25.invoke.return_value = [docs[1]]
    
    vector_manager.hybrid_retriever.vector_retriever = mock_vec
    vector_manager.hybrid_retriever.bm25_retriever = mock_bm25
    
    # Test search_hybrid call
    results = vector_manager.search_hybrid("gato")

    assert len(results) > 0
    # O gato deve estar presente (vindo do vector_retriever)
    assert any(d.page_content == "O gato está no telhado" for d in results)
    # O cachorro deve estar presente (vindo do bm25_retriever)
    assert any(d.page_content == "O cachorro está no jardim" for d in results)
    
    mock_vec.invoke.assert_called()
    mock_bm25.invoke.assert_called()


if __name__ == "__main__":
    # For manual verification if needed
    pass
