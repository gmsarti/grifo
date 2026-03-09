import pytest
from unittest.mock import patch, MagicMock
from app.data_source.vector_store import VectorStoreManager
from langchain_core.documents import Document


@pytest.fixture
def vector_manager():
    with (
        patch("app.data_source.vector_store.Chroma"),
        patch("app.data_source.vector_store.OpenAIEmbeddings"),
    ):
        return VectorStoreManager()


@patch("app.data_source.loaders.FileIngestionService.process_file")
def test_ingest_file(mock_process, vector_manager):
    # Mock documents returned by service
    mock_process.return_value = [
        Document(page_content="file content", metadata={"source": "test.txt"})
    ]

    # Mock Chroma add_documents
    vector_manager.vector_store.add_documents = MagicMock()

    vector_manager.ingest_file("test.txt")

    mock_process.assert_called_once_with("test.txt")
    vector_manager.vector_store.add_documents.assert_called_once()
    args, _ = vector_manager.vector_store.add_documents.call_args
    assert args[0][0].page_content == "file content"


@patch("app.data_source.loaders.WebIngestionService.process_url")
def test_ingest_url(mock_process, vector_manager):
    # Mock documents returned by service
    mock_process.return_value = [
        Document(page_content="web content", metadata={"source": "http://example.com"})
    ]

    # Mock Chroma add_documents
    vector_manager.vector_store.add_documents = MagicMock()

    vector_manager.ingest_url("http://example.com")

    mock_process.assert_called_once_with("http://example.com")
    vector_manager.vector_store.add_documents.assert_called_once()
    args, _ = vector_manager.vector_store.add_documents.call_args
    assert args[0][0].page_content == "web content"
