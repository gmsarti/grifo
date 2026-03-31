from unittest.mock import MagicMock, patch

import pytest

from app.processing.router_chain import RouterDecision, get_router_chain


# ── RouterDecision schema ─────────────────────────────────────────────────────


def test_router_decision_reflexion_intent_is_valid():
    decision = RouterDecision(intent="reflexion")
    assert decision.intent == "reflexion"
    assert decision.zona is None
    assert decision.mobiliario == []


def test_router_decision_arq_extract_with_zona_and_mobiliario():
    decision = RouterDecision(
        intent="arq_extract", zona="quarto", mobiliario=["cama", "guarda-roupa"]
    )
    assert decision.intent == "arq_extract"
    assert decision.zona == "quarto"
    assert decision.mobiliario == ["cama", "guarda-roupa"]


def test_router_decision_zona_defaults_to_none():
    decision = RouterDecision(intent="arq_extract")
    assert decision.zona is None


def test_router_decision_mobiliario_defaults_to_empty_list():
    decision = RouterDecision(intent="reflexion")
    assert decision.mobiliario == []


# ── get_router_chain ──────────────────────────────────────────────────────────


def test_get_router_chain_calls_with_structured_output():
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    with patch("app.processing.router_chain.get_fast_model", return_value=mock_llm):
        chain = get_router_chain()

    assert chain is not None
    mock_llm.with_structured_output.assert_called_once_with(RouterDecision)


def test_get_router_chain_uses_fast_model_not_reasoner():
    """Classificação de intenção não exige modelo de alta capacidade."""
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    # router_chain.py importa apenas get_fast_model — patchamos no ponto de uso
    with patch("app.processing.router_chain.get_fast_model", return_value=mock_llm) as mock_fast:
        get_router_chain()

    mock_fast.assert_called_once()


@pytest.mark.prompt_contract
def test_router_chain_system_prompt_contains_valid_zone_names():
    """O system prompt do router deve listar as zonas válidas para o LLM."""
    from app.processing.router_chain import _SYSTEM

    for zona in ("quarto", "sala", "cozinha", "banheiro"):
        assert zona in _SYSTEM, f"Zona '{zona}' ausente no system prompt do router"


@pytest.mark.prompt_contract
def test_router_chain_system_prompt_defines_arq_extract_intent():
    """O system prompt deve descrever o que caracteriza a intenção 'arq_extract'."""
    from app.processing.router_chain import _SYSTEM

    arq_keywords = ["arq_extract", "restrição", "posicionamento", "arranjo", "encostado"]
    has_arq_description = any(kw in _SYSTEM for kw in arq_keywords)
    assert has_arq_description, (
        "O system prompt do router não descreve a intenção 'arq_extract'. "
        f"Esperava pelo menos uma de: {arq_keywords}"
    )
