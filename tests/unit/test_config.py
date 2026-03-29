import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _make_settings(**kwargs) -> Settings:
    defaults = {
        "DATABASE_URL": "sqlite+aiosqlite:///./data/sql_app.db",
        "SECRET_KEY": "uma-chave-forte-qualquer-de-pelo-menos-32-chars!",
    }
    defaults.update(kwargs)
    return Settings.model_validate(defaults)


def test_secret_key_com_valor_forte_e_aceita():
    s = _make_settings(
        SECRET_KEY="07cb8299ad2e1f6e732dc561c02482fa8e162b76a69f49dcbe1e0b9a2a681631"
    )
    assert (
        s.SECRET_KEY
        == "07cb8299ad2e1f6e732dc561c02482fa8e162b76a69f49dcbe1e0b9a2a681631"
    )


@pytest.mark.parametrize(
    "insecure",
    [
        "supersecretkey",
        "changeme",
        "secret",
        "",
        "your-secret-key",
        "SUPERSECRETKEY",
        "Changeme",
    ],
)
def test_secret_key_com_valor_inseguro_levanta_erro(insecure):
    with pytest.raises(ValidationError, match="SECRET_KEY insegura"):
        _make_settings(SECRET_KEY=insecure)


def test_secret_key_ausente_levanta_erro():
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
