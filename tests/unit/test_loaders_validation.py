import pytest
import os
from pathlib import Path
from app.data_source.loaders import FileIngestionService, WebIngestionService

@pytest.fixture
def file_service():
    return FileIngestionService()

@pytest.fixture
def web_service():
    return WebIngestionService()

def test_validate_file_not_found(file_service):
    with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
        file_service.validate_file("non_existent_file.pdf")

def test_validate_file_empty(file_service, tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    with pytest.raises(ValueError, match="O arquivo está vazio"):
        file_service.validate_file(str(empty_file))

def test_validate_file_unsupported_ext(file_service, tmp_path):
    bad_file = tmp_path / "script.exe"
    bad_file.write_text("not a script")
    with pytest.raises(ValueError, match="Extensão não suportada"):
        file_service.validate_file(str(bad_file))

def test_validate_file_valid(file_service, tmp_path):
    valid_file = tmp_path / "valid.md"
    valid_file.write_text("# Hello")
    ext = file_service.validate_file(str(valid_file))
    assert ext == ".md"

def test_process_file_runtime_error_on_parsing(file_service, tmp_path, mocker):
    # Mocking TextLoader to raise an exception during load
    mocker.patch("app.data_source.loaders.TextLoader.load", side_effect=Exception("Parsing failed"))
    
    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("content")
    
    with pytest.raises(RuntimeError, match="Falha no parsing do arquivo .txt"):
        file_service.process_file(str(valid_file))

def test_process_url_runtime_error(web_service, mocker):
    mocker.patch("app.data_source.loaders.WebBaseLoader.load", side_effect=Exception("Connection error"))
    
    with pytest.raises(RuntimeError, match="Falha ao carregar conteúdo da URL"):
        web_service.process_url("https://invalid-url.com")
