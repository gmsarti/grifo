"""
Testes para B-003: reconstrução do índice BM25 no startup e fallback observável.

Critérios de aceite:
- Após restart, busca híbrida em projeto com docs já indexados usa BM25 corretamente.
- O fallback para busca vetorial gera um log de warning.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.data_source.vector_store import VectorStoreManager


def _make_chroma_get_result(texts: list[str], metadatas: list[dict] | None = None):
    """Helper: retorna o formato que Chroma.get() retorna."""
    return {
        "documents": texts,
        "metadatas": metadatas or [{}] * len(texts),
    }


@pytest.fixture
def chroma_mock():
    """Mock do Chroma com coleção vazia por padrão."""
    mock = MagicMock()
    mock.get.return_value = _make_chroma_get_result([])
    mock.as_retriever.return_value = MagicMock()
    return mock


def _make_manager(chroma_mock):
    """Cria VectorStoreManager com Chroma e embeddings mockados."""
    with (
        patch("app.data_source.vector_store.Chroma", return_value=chroma_mock),
        patch("app.data_source.vector_store.OpenAIEmbeddings"),
    ):
        return VectorStoreManager()


# ── Reconstrução no startup ───────────────────────────────────────────────────


def test_bm25_rebuilt_when_chroma_has_documents(chroma_mock):
    """Se o ChromaDB já tem documentos, o BM25 deve ser inicializado no __init__."""
    chroma_mock.get.return_value = _make_chroma_get_result(
        ["O gato está no telhado", "O cachorro está no jardim"],
        [{"source": "doc1.txt"}, {"source": "doc1.txt"}],
    )

    vm = _make_manager(chroma_mock)

    assert vm.bm25_retriever is not None, (
        "bm25_retriever deve ser reconstruído a partir do ChromaDB no __init__."
    )
    assert vm.hybrid_retriever is not None, (
        "hybrid_retriever deve ser reconstruído a partir do ChromaDB no __init__."
    )
    assert len(vm._all_documents) == 2


def test_bm25_not_rebuilt_when_chroma_is_empty(chroma_mock):
    """Se o ChromaDB está vazio, nenhum erro deve ocorrer e bm25_retriever permanece None."""
    chroma_mock.get.return_value = _make_chroma_get_result([])

    vm = _make_manager(chroma_mock)

    assert vm.bm25_retriever is None
    assert vm.hybrid_retriever is None
    assert vm._all_documents == []


def test_rebuilt_bm25_returns_relevant_results(chroma_mock):
    """BM25 reconstruído a partir do Chroma deve retornar docs relevantes por keyword."""
    chroma_mock.get.return_value = _make_chroma_get_result(
        [
            "FastAPI é um framework Python",
            "Django também é Python",
            "Go é uma linguagem compilada",
        ],
        [{}, {}, {}],
    )

    vm = _make_manager(chroma_mock)
    results = vm.search_bm25("framework Python")

    assert len(results) > 0
    contents = " ".join(r.page_content for r in results)
    assert "Python" in contents


# ── Fallback observável ───────────────────────────────────────────────────────


def test_search_hybrid_logs_warning_on_fallback(chroma_mock, caplog):
    """
    Quando hybrid_retriever não existe, search_hybrid deve logar um warning
    antes de cair para busca vetorial pura.
    """
    chroma_mock.get.return_value = _make_chroma_get_result([])
    chroma_mock.similarity_search.return_value = [
        Document(page_content="resultado vetorial")
    ]

    vm = _make_manager(chroma_mock)
    assert vm.hybrid_retriever is None  # pré-condição

    with caplog.at_level(logging.WARNING, logger="app.data_source.vector_store"):
        results = vm.search_hybrid("qualquer query")

    assert any(
        "BM25" in r.message or "fallback" in r.message.lower() for r in caplog.records
    ), "search_hybrid deve emitir um warning quando faz fallback para busca vetorial."
    assert results == [Document(page_content="resultado vetorial")]


def test_search_hybrid_uses_hybrid_retriever_when_available(chroma_mock):
    """Quando BM25 foi reconstruído, search_hybrid deve usar o HybridRetriever."""
    expected = [Document(page_content="resultado híbrido")]

    chroma_mock.get.return_value = _make_chroma_get_result(
        ["documento existente"],
        [{}],
    )

    mock_hybrid = MagicMock()
    mock_hybrid.invoke.return_value = expected

    with (
        patch("app.data_source.vector_store.Chroma", return_value=chroma_mock),
        patch("app.data_source.vector_store.OpenAIEmbeddings"),
        patch("app.data_source.vector_store.HybridRetriever", return_value=mock_hybrid),
    ):
        vm = VectorStoreManager()

    results = vm.search_hybrid("query")

    mock_hybrid.invoke.assert_called_once()
    assert results == expected
    chroma_mock.similarity_search.assert_not_called()
