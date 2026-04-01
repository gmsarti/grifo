"""
Testes unitários para app/processing/arq_text_converter.py.

Cobre:
  - Lista vazia
  - Padrão desconhecido (fallback)
  - Cada tipo de restrição, preferência e grid
  - Estruturas especiais: exceto, multiplo, erro-objeto, erro-lado
"""

import pytest

from app.processing.arq_text_converter import PatternToText, padroes_para_texto


@pytest.fixture()
def converter():
    return PatternToText()


# ── Lista vazia e fallback ────────────────────────────────────────────────────


def test_empty_list_returns_nenhum_padrao(converter):
    assert converter.converter([]) == "Nenhum padrão identificado."


def test_unknown_tipo_returns_fallback(converter):
    result = converter.converter([{"tipo": "xpto", "padrao": "foo"}])
    assert "desconhecido" in result.lower()


def test_unknown_padrao_within_valid_tipo_returns_fallback(converter):
    result = converter.converter([{"tipo": "restricao", "padrao": "voar"}])
    assert "desconhecido" in result.lower()


# ── Restrições ────────────────────────────────────────────────────────────────


def test_circulacao(converter):
    p = {"tipo": "restricao", "padrao": "circulacao", "objeto": {"nome": "cama"}, "gap": 60}
    assert "60cm" in converter.converter([p])
    assert "cama" in converter.converter([p])


def test_dentro_zona(converter):
    p = {"tipo": "restricao", "padrao": "dentro_zona", "objeto": {"nome": "cama"}, "zona": "quarto"}
    result = converter.converter([p])
    assert "cama" in result
    assert "quarto" in result


def test_dentro_objeto(converter):
    p = {
        "tipo": "restricao",
        "padrao": "dentro_objeto",
        "objeto_pequeno": {"nome": "candelabro"},
        "objeto_grande": {"nome": "mesa"},
    }
    result = converter.converter([p])
    assert "candelabro" in result
    assert "mesa" in result


def test_encostado_with_lado(converter):
    p = {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"}
    result = converter.converter([p])
    assert "cama" in result
    assert "encostado" in result


def test_encostado_defaults_to_fundos_when_no_lado(converter):
    p = {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}}
    result = converter.converter([p])
    assert "fundos" in result


def test_nao_encostado(converter):
    p = {"tipo": "restricao", "padrao": "nao_encostado", "objeto": {"nome": "sofa"}, "lado": "frente"}
    result = converter.converter([p])
    assert "não" in result
    assert "sofa" in result


def test_distancia_maxima(converter):
    p = {
        "tipo": "restricao",
        "padrao": "distancia_maxima",
        "objeto1": {"nome": "sofa"},
        "objeto2": {"nome": "tv"},
        "gap": 300,
    }
    result = converter.converter([p])
    assert "300cm" in result
    assert "máxima" in result


def test_distancia_minima(converter):
    p = {
        "tipo": "restricao",
        "padrao": "distancia_minima",
        "objeto1": {"nome": "cama"},
        "objeto2": {"nome": "guarda-roupa"},
        "gap": 80,
    }
    result = converter.converter([p])
    assert "80cm" in result
    assert "mínima" in result


def test_adjacente(converter):
    p = {
        "tipo": "restricao",
        "padrao": "adjacente",
        "objeto1": {"nome": "criado-mudo"},
        "objeto2": {"nome": "cama"},
    }
    result = converter.converter([p])
    assert "criado-mudo" in result
    assert "cama" in result
    assert "encostado" in result


def test_virado_para_objeto(converter):
    p = {
        "tipo": "restricao",
        "padrao": "virado_para_objeto",
        "objeto1": {"nome": "sofa"},
        "lado": "frente",
        "objeto2": {"nome": "tv"},
    }
    result = converter.converter([p])
    assert "sofa" in result
    assert "tv" in result
    assert "virado" in result


def test_paralelo(converter):
    p = {"tipo": "restricao", "padrao": "paralelo", "objeto": {"nome": "sofa"}}
    result = converter.converter([p])
    assert "direção" in result


def test_obstrucao(converter):
    p = {
        "tipo": "restricao",
        "padrao": "obstrucao",
        "objeto1": {"nome": "cama"},
        "lado": "frente",
        "objeto2": {"nome": "janela"},
    }
    result = converter.converter([p])
    assert "obstrução" in result


def test_nao_obstrucao(converter):
    p = {
        "tipo": "restricao",
        "padrao": "nao_obstrucao",
        "objeto1": {"nome": "sofa"},
        "lado": "frente",
        "objeto2": {"nome": "tv"},
    }
    result = converter.converter([p])
    assert "Não" in result
    assert "obstrução" in result


def test_nao_sobreposicao_core(converter):
    p = {"tipo": "restricao", "padrao": "nao_sobreposicao_core", "objeto": {"nome": "cama"}}
    result = converter.converter([p])
    assert "core" in result
    assert "sobreposição" in result


def test_nao_sobreposicao_acesso(converter):
    p = {"tipo": "restricao", "padrao": "nao_sobreposicao_acesso", "objeto": {"nome": "cama"}}
    result = converter.converter([p])
    assert "acesso" in result


def test_nao_sobreposicao_par(converter):
    p = {
        "tipo": "restricao",
        "padrao": "nao_sobreposicao_par",
        "objeto_core": {"nome": "cama"},
        "objeto_acesso": {"nome": "guarda-roupa"},
    }
    result = converter.converter([p])
    assert "cama" in result
    assert "guarda-roupa" in result


def test_projecao_ortogonal(converter):
    p = {
        "tipo": "restricao",
        "padrao": "projecao_ortogonal",
        "objeto_sombra": {"nome": "sofa"},
        "objeto_sobreado": {"nome": "tv"},
        "proporcao": 75,
    }
    result = converter.converter([p])
    assert "75%" in result
    assert "projeção ortogonal" in result


# ── Preferências ──────────────────────────────────────────────────────────────


def test_preferencia_distancia_maxima(converter):
    p = {
        "tipo": "preferencia",
        "padrao": "preferencia_distancia_maxima",
        "objeto1": {"nome": "sofa"},
        "objeto2": {"nome": "tv"},
        "gap": 300,
    }
    result = converter.converter([p])
    assert "Preferencialmente" in result
    assert "300cm" in result
    assert "máxima" in result


def test_preferencia_distancia_minima(converter):
    p = {
        "tipo": "preferencia",
        "padrao": "preferencia_distancia_minima",
        "objeto1": {"nome": "cama"},
        "objeto2": {"nome": "porta"},
        "gap": 90,
    }
    result = converter.converter([p])
    assert "Preferencialmente" in result
    assert "90cm" in result


def test_preferencia_projecao_ortogonal(converter):
    p = {
        "tipo": "preferencia",
        "padrao": "preferencia_projecao_ortogonal",
        "objeto_sombra": {"nome": "sofa"},
        "objeto_sobreado": {"nome": "tv"},
        "proporcao": 50,
    }
    result = converter.converter([p])
    assert "Preferencialmente" in result
    assert "50%" in result


def test_preferencia_separacao_maxima(converter):
    p = {
        "tipo": "preferencia",
        "padrao": "preferencia_separacao_maxima",
        "objeto1": {"nome": "cama"},
        "objeto2": {"nome": "porta"},
    }
    result = converter.converter([p])
    assert "Preferencialmente" in result
    assert "longe" in result


def test_preferencia_escolha(converter):
    p = {
        "tipo": "preferencia",
        "padrao": "preferencia_escolha",
        "objeto_preferencial": {"nome": "cama"},
        "objeto_outro": {"nome": "sofa"},
    }
    result = converter.converter([p])
    assert "Preferencialmente" in result
    assert "vez de" in result


# ── Grids ─────────────────────────────────────────────────────────────────────


def test_grid_espaco_with_x_and_y(converter):
    p = {"tipo": "grid", "padrao": "grid_espaco", "objeto": {"nome": "sofa"}, "X": 60, "Y": 90}
    result = converter.converter([p])
    assert "60cm" in result
    assert "90cm" in result
    assert "reticulado" in result


def test_grid_espaco_uses_x_when_y_missing(converter):
    p = {"tipo": "grid", "padrao": "grid_espaco", "objeto": {"nome": "sofa"}, "X": 60}
    result = converter.converter([p])
    assert result.count("60cm") == 2


def test_grid_linha(converter):
    p = {"tipo": "grid", "padrao": "grid_linha", "objeto": {"nome": "sofa"}, "X": 30}
    result = converter.converter([p])
    assert "30cm" in result
    assert "parede" in result


# ── Estruturas especiais ──────────────────────────────────────────────────────


def test_objeto_com_exceto(converter):
    p = {
        "tipo": "restricao",
        "padrao": "dentro_zona",
        "objeto": {"nome": "movel", "exceto": "sofa"},
        "zona": "quarto",
    }
    result = converter.converter([p])
    assert "movel" in result
    assert "exceto" in result
    assert "sofa" in result


def test_objeto_com_multiplo(converter):
    p = {
        "tipo": "restricao",
        "padrao": "paralelo",
        "objeto": {"multiplo": [{"nome": "cama"}, {"nome": "sofa"}]},
    }
    result = converter.converter([p])
    assert "cama" in result
    assert "sofa" in result


def test_objeto_com_erro_desconhecido(converter):
    p = {
        "tipo": "restricao",
        "padrao": "virado_para_objeto",
        "objeto1": {"nome": "cama"},
        "lado": "frente",
        "objeto2": {"erro": "objeto_desconhecido", "texto": "pentiadeira"},
    }
    result = converter.converter([p])
    assert "pentiadeira" in result


def test_lado_com_erro_desconhecido(converter):
    p = {
        "tipo": "restricao",
        "padrao": "encostado",
        "objeto": {"nome": "mesa"},
        "lado": {"erro": "lado_desconhecido", "texto": "pe"},
    }
    result = converter.converter([p])
    assert "pe" in result


# ── Múltiplos padrões ─────────────────────────────────────────────────────────


def test_multiple_patterns_joined_by_space(converter):
    padroes = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"},
        {"tipo": "restricao", "padrao": "circulacao", "objeto": {"nome": "cama"}, "gap": 60},
    ]
    result = converter.converter(padroes)
    assert "cama" in result
    assert "encostado" in result
    assert "60cm" in result


# ── Função pública ────────────────────────────────────────────────────────────


def test_padroes_para_texto_delegates_to_converter():
    padroes = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"}
    ]
    result = padroes_para_texto(padroes)
    assert "cama" in result
    assert isinstance(result, str)


# ── padroes_para_markdown ─────────────────────────────────────────────────────

from app.processing.arq_text_converter import padroes_para_markdown


def test_padroes_para_markdown_empty_returns_nenhum_padrao():
    result = padroes_para_markdown([])
    assert "Nenhum padrão identificado." in result


def test_padroes_para_markdown_includes_zona_header():
    result = padroes_para_markdown([], zona="quarto", mobiliario=["cama"])
    assert "quarto" in result
    assert "cama" in result


def test_padroes_para_markdown_restricoes_section_header():
    padroes = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"}
    ]
    result = padroes_para_markdown(padroes)
    assert "Restrições" in result


def test_padroes_para_markdown_uses_bullet_points():
    padroes = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"}
    ]
    result = padroes_para_markdown(padroes)
    assert "- " in result


def test_padroes_para_markdown_groups_by_tipo():
    padroes = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"},
        {"tipo": "preferencia", "padrao": "preferencia_separacao_maxima",
         "objeto1": {"nome": "cama"}, "objeto2": {"nome": "porta"}},
    ]
    result = padroes_para_markdown(padroes)
    assert "Restrições" in result
    assert "Preferências" in result


def test_padroes_para_markdown_ignores_object_refs_without_tipo():
    """Referências soltas de objeto (sem 'tipo') não viram frases."""
    padroes = [
        {"nome": "cama"},  # referência solta — sem tipo/padrao
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"},
    ]
    result = padroes_para_markdown(padroes)
    assert result.count("- ") == 1  # só a frase do encostado
