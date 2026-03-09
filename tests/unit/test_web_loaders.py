from unittest.mock import patch
from app.data_source.loaders import WebIngestionService
from langchain_core.documents import Document


@patch("app.data_source.loaders.WebBaseLoader")
def test_process_url(mock_web_loader):
    service = WebIngestionService()

    # Mocking loader.load()
    mock_loader_instance = mock_web_loader.return_value
    mock_loader_instance.load.return_value = [
        Document(page_content="Web content", metadata={"source": "http://example.com"})
    ]

    docs = service.process_url("http://example.com")

    assert len(docs) > 0
    assert docs[0].page_content == "Web content"
    mock_web_loader.assert_called_once_with("http://example.com")
    mock_loader_instance.load.assert_called_once()
