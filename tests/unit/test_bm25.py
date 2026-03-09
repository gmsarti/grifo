import pytest
from unittest.mock import patch
from app.data_source.vector_store import VectorStoreManager
from langchain_core.documents import Document


@pytest.fixture
def vector_manager():
    with (
        patch("app.data_source.vector_store.Chroma"),
        patch("app.data_source.vector_store.OpenAIEmbeddings"),
    ):
        vm = VectorStoreManager()
        return vm


def test_bm25_retrieval(vector_manager):
    docs = [
        Document(page_content="O gato está no telhado", metadata={"id": 1}),
        Document(page_content="O cachorro está no jardim", metadata={"id": 2}),
        Document(page_content="A maçã é vermelha", metadata={"id": 3}),
    ]

    # Adicionando documentos (isso inicializa o BM25)
    vector_manager.add_documents(docs)

    # Testando busca por palavra-chave exata
    results = vector_manager.search_bm25("gato")
    assert len(results) > 0
    assert "gato" in results[0].page_content

    results = vector_manager.search_bm25("jardim")
    assert len(results) > 0
    assert "jardim" in results[0].page_content


def test_bm25_empty_retriever(vector_manager):
    # Sem documentos, o retriever deve retornar lista vazia
    results = vector_manager.search_bm25("teste")
    assert results == []
