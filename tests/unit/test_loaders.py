import pytest
from unittest.mock import MagicMock, patch
from app.data_source.loaders import FileIngestionService
from langchain_core.documents import Document


@patch("os.path.exists")
def test_file_ingestion_service_unsupported_ext(mock_exists):
    mock_exists.return_value = True
    service = FileIngestionService()
    with pytest.raises(ValueError, match="Unsupported file extension"):
        service.process_file("test.unknown")


@patch("app.data_source.loaders.PyPDFLoader")
@patch("os.path.exists")
def test_process_pdf(mock_exists, mock_pdf_loader):
    mock_exists.return_value = True
    service = FileIngestionService()

    # Mocking loader.load()
    mock_loader_instance = mock_pdf_loader.return_value
    mock_loader_instance.load.return_value = [Document(page_content="PDF content")]

    docs = service.process_file("test.pdf")

    assert len(docs) > 0
    mock_pdf_loader.assert_called_once_with("test.pdf")
    mock_loader_instance.load.assert_called_once()


@patch("app.data_source.loaders.TextLoader")
@patch("os.path.exists")
def test_process_txt(mock_exists, mock_text_loader):
    mock_exists.return_value = True
    service = FileIngestionService()

    mock_loader_instance = mock_text_loader.return_value
    mock_loader_instance.load.return_value = [Document(page_content="TXT content")]

    docs = service.process_file("test.txt")

    assert len(docs) > 0
    mock_text_loader.assert_called_once_with("test.txt")
    mock_loader_instance.load.assert_called_once()
