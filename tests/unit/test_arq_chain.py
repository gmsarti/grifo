import json
from unittest.mock import MagicMock, patch

import pytest

from app.processing.arq_chain import get_arq_extractor_chain, render_arq_prompt
from app.schemas.arq_schemas import PadroesExtraidos


# ── render_arq_prompt ─────────────────────────────────────────────────────────


def test_render_arq_prompt_substitutes_objetos():
    objetos = {"cama": ["solteiro", "casal"]}
    result = render_arq_prompt(objetos=objetos, lados=[], zonas=[], texto="x")
    assert json.dumps(objetos, ensure_ascii=False, indent=2) in result
    assert "$objetos" not in result


def test_render_arq_prompt_substitutes_lados():
    lados = [{"nome": "cama", "fundos": "cabeceira"}]
    result = render_arq_prompt(objetos={}, lados=lados, zonas=[], texto="x")
    assert json.dumps(lados, ensure_ascii=False) in result
    assert "$lados" not in result


def test_render_arq_prompt_substitutes_zonas():
    zonas = ["quarto", "sala"]
    result = render_arq_prompt(objetos={}, lados=[], zonas=zonas, texto="x")
    assert json.dumps(zonas, ensure_ascii=False) in result
    assert "$zonas" not in result


def test_render_arq_prompt_substitutes_texto():
    texto = "A cama deve estar encostada na parede dos fundos"
    result = render_arq_prompt(objetos={}, lados=[], zonas=[], texto=texto)
    assert texto in result
    assert "$texto" not in result


def test_render_arq_prompt_no_remaining_dollar_variables():
    """Todas as variáveis $-prefixadas devem ser substituídas."""
    result = render_arq_prompt(
        objetos={"cama": []},
        lados=[{"nome": "cama", "fundos": "cabeceira"}],
        zonas=["quarto"],
        texto="A cama encostada",
    )
    for var in ("$objetos", "$lados", "$zonas", "$texto"):
        assert var not in result, f"Variável '{var}' não foi substituída"


def test_render_arq_prompt_preserves_non_variable_content():
    """O conteúdo fixo do prompt (instruções) deve permanecer intacto."""
    result = render_arq_prompt(objetos={}, lados=[], zonas=[], texto="x")
    # O prompt define padrões como "circulacao", "encostado" etc.
    assert "circulacao" in result or "restricao" in result


# ── get_arq_extractor_chain ───────────────────────────────────────────────────


def test_get_arq_extractor_chain_calls_with_structured_output():
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    with patch("app.processing.arq_chain.get_reasoner", return_value=mock_llm):
        chain = get_arq_extractor_chain()

    assert chain is not None
    mock_llm.with_structured_output.assert_called_once_with(PadroesExtraidos)


def test_get_arq_extractor_chain_uses_reasoner_not_fast_model():
    """Extração estruturada com gramática complexa usa o modelo de maior capacidade."""
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    # arq_chain.py importa apenas get_reasoner — patchamos no ponto de uso
    with patch("app.processing.arq_chain.get_reasoner", return_value=mock_llm) as mock_reasoner:
        get_arq_extractor_chain()

    mock_reasoner.assert_called_once()


@pytest.mark.prompt_contract
def test_get_arq_extractor_chain_prompt_accepts_prompt_text_variable():
    """O template da chain deve usar {prompt_text} como única variável de entrada."""
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    with patch("app.processing.arq_chain.get_reasoner", return_value=mock_llm):
        chain = get_arq_extractor_chain()

    prompt_template = chain.first
    assert "prompt_text" in prompt_template.input_variables
