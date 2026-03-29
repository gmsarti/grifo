import pytest
from pydantic import ValidationError

from app.schemas.project import MAX_SYSTEM_PROMPT_LENGTH, ProjectBase, ProjectCreate


def test_system_prompt_none_aceito():
    p = ProjectCreate(name="Proj", system_prompt=None)
    assert p.system_prompt is None


def test_system_prompt_vazio_aceito():
    p = ProjectCreate(name="Proj", system_prompt="")
    assert p.system_prompt == ""


def test_system_prompt_no_limite_aceito():
    prompt = "a" * MAX_SYSTEM_PROMPT_LENGTH
    p = ProjectCreate(name="Proj", system_prompt=prompt)
    assert len(p.system_prompt) == MAX_SYSTEM_PROMPT_LENGTH


def test_system_prompt_acima_do_limite_levanta_erro():
    prompt = "a" * (MAX_SYSTEM_PROMPT_LENGTH + 1)
    with pytest.raises(ValidationError, match="system_prompt não pode exceder"):
        ProjectCreate(name="Proj", system_prompt=prompt)


def test_system_prompt_acima_do_limite_informa_tamanho_recebido():
    prompt = "x" * (MAX_SYSTEM_PROMPT_LENGTH + 500)
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(name="Proj", system_prompt=prompt)
    assert str(MAX_SYSTEM_PROMPT_LENGTH + 500) in str(exc_info.value)


def test_system_prompt_valido_em_project_base():
    p = ProjectBase(system_prompt="Você é um assistente útil.")
    assert p.system_prompt == "Você é um assistente útil."


def test_project_update_herda_validacao():
    from app.schemas.project import ProjectUpdate

    prompt = "b" * (MAX_SYSTEM_PROMPT_LENGTH + 1)
    with pytest.raises(ValidationError):
        ProjectUpdate(system_prompt=prompt)
