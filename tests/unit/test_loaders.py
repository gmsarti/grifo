from unittest.mock import patch

import pytest
from langchain_core.documents import Document

from app.data_source.loaders import FileIngestionService


@patch("os.stat")
@patch("os.path.exists")
def test_file_ingestion_service_unsupported_ext(mock_exists, mock_stat):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1024  # 1KB — abaixo de qualquer limite
    service = FileIngestionService()
    with pytest.raises(ValueError, match="Extensão não suportada"):
        service.process_file("test.unknown")


@patch("app.data_source.loaders.PyPDFLoader")
@patch("os.stat")
@patch("os.path.exists")
def test_process_pdf(mock_exists, mock_stat, mock_pdf_loader):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1024  # 1KB — abaixo de qualquer limite
    service = FileIngestionService()

    mock_loader_instance = mock_pdf_loader.return_value
    mock_loader_instance.load.return_value = [Document(page_content="PDF content")]

    docs = service.process_file("test.pdf")

    assert len(docs) > 0
    mock_pdf_loader.assert_called_once_with("test.pdf")
    mock_loader_instance.load.assert_called_once()


@patch("app.data_source.loaders.TextLoader")
@patch("os.stat")
@patch("os.path.exists")
def test_process_txt(mock_exists, mock_stat, mock_text_loader):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1024  # 1KB — abaixo de qualquer limite
    service = FileIngestionService()

    mock_loader_instance = mock_text_loader.return_value
    mock_loader_instance.load.return_value = [Document(page_content="TXT content")]

    docs = service.process_file("test.txt")

    assert len(docs) > 0
    mock_text_loader.assert_called_once_with("test.txt")
    mock_loader_instance.load.assert_called_once()
