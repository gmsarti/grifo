import pytest

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


def test_validate_file_acima_do_limite_levanta_erro(file_service, tmp_path, mocker):
    big_file = tmp_path / "big.txt"
    big_file.write_text("x")
    mocker.patch(
        "app.data_source.loaders.settings",
        MAX_FILE_SIZE_MB=10,
    )
    # Simula um arquivo de 11MB
    mocker.patch("os.stat").return_value.st_size = 11 * 1024 * 1024

    with pytest.raises(ValueError, match="Arquivo muito grande"):
        file_service.validate_file(str(big_file))


def test_validate_file_acima_do_limite_informa_tamanho_e_limite(
    file_service, tmp_path, mocker
):
    big_file = tmp_path / "big.pdf"
    big_file.write_text("x")
    mocker.patch("app.data_source.loaders.settings", MAX_FILE_SIZE_MB=50)
    mocker.patch("os.stat").return_value.st_size = 75 * 1024 * 1024

    with pytest.raises(ValueError, match="75.0MB") as exc_info:
        file_service.validate_file(str(big_file))
    assert "50MB" in str(exc_info.value)


def test_validate_file_exatamente_no_limite_e_aceito(file_service, tmp_path, mocker):
    file = tmp_path / "onlimit.txt"
    file.write_text("x")
    mocker.patch("app.data_source.loaders.settings", MAX_FILE_SIZE_MB=50)
    mocker.patch("os.stat").return_value.st_size = 50 * 1024 * 1024

    # Não deve lançar exceção (limite é exclusivo: > MAX, não >=)
    ext = file_service.validate_file(str(file))
    assert ext == ".txt"


def test_max_file_size_mb_configuravel_via_settings():
    from app.core.config import settings

    assert hasattr(settings, "MAX_FILE_SIZE_MB")
    assert isinstance(settings.MAX_FILE_SIZE_MB, int)
    assert settings.MAX_FILE_SIZE_MB > 0


def test_process_file_runtime_error_on_parsing(file_service, tmp_path, mocker):
    # Mocking TextLoader to raise an exception during load
    mocker.patch(
        "app.data_source.loaders.TextLoader.load",
        side_effect=Exception("Parsing failed"),
    )

    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("content")

    with pytest.raises(RuntimeError, match="Falha no parsing do arquivo .txt"):
        file_service.process_file(str(valid_file))


def test_process_url_runtime_error(web_service, mocker):
    mocker.patch(
        "app.data_source.loaders.WebBaseLoader.load",
        side_effect=Exception("Connection error"),
    )

    with pytest.raises(RuntimeError, match="Falha ao carregar conteúdo da URL"):
        web_service.process_url("https://invalid-url.com")
