from app.data.arq_vocabulary import (
    LADOS_POR_OBJETO,
    OBJETOS_POR_ZONA,
    ZONAS,
    get_lados_for_objects,
)


# ── ZONAS ─────────────────────────────────────────────────────────────────────


def test_zonas_contains_quarto():
    assert "quarto" in ZONAS


def test_zonas_contains_sala():
    assert "sala" in ZONAS


def test_zonas_contains_cozinha():
    assert "cozinha" in ZONAS


def test_zonas_contains_banheiro():
    assert "banheiro" in ZONAS


# ── OBJETOS_POR_ZONA ──────────────────────────────────────────────────────────


def test_objetos_por_zona_every_zona_has_at_least_one_object():
    for zona in ZONAS:
        assert zona in OBJETOS_POR_ZONA
        assert len(OBJETOS_POR_ZONA[zona]) > 0, f"Zona '{zona}' não tem objetos"


def test_objetos_por_zona_banheiro_does_not_contain_fogao():
    """Fogão não deve estar disponível no banheiro — restrição de domínio."""
    assert "fogao" not in OBJETOS_POR_ZONA["banheiro"]


def test_objetos_por_zona_banheiro_does_not_contain_cama():
    assert "cama" not in OBJETOS_POR_ZONA["banheiro"]


def test_objetos_por_zona_cozinha_does_not_contain_cama():
    assert "cama" not in OBJETOS_POR_ZONA["cozinha"]


def test_objetos_por_zona_quarto_contains_cama():
    assert "cama" in OBJETOS_POR_ZONA["quarto"]


# ── get_lados_for_objects ─────────────────────────────────────────────────────


def test_get_lados_for_objects_returns_only_requested_objects():
    result = get_lados_for_objects(["cama"])
    names = [entry["nome"] for entry in result]
    assert names == ["cama"]


def test_get_lados_for_objects_excludes_objects_not_in_input():
    """Geladeira tem aliases — não deve aparecer se não foi solicitada."""
    result = get_lados_for_objects(["cama"])
    names = [entry["nome"] for entry in result]
    assert "geladeira" not in names


def test_get_lados_for_objects_excludes_objects_without_defined_aliases():
    """criado-mudo não possui aliases — lista deve ser vazia."""
    result = get_lados_for_objects(["criado-mudo"])
    assert result == []


def test_get_lados_for_objects_returns_correct_alias_for_cama_fundos():
    result = get_lados_for_objects(["cama"])
    entry = result[0]
    assert entry["fundos"] == "cabeceira"


def test_get_lados_for_objects_returns_correct_alias_for_cama_frente():
    result = get_lados_for_objects(["cama"])
    entry = result[0]
    assert entry["frente"] == "pés da cama"


def test_get_lados_for_objects_returns_correct_alias_for_geladeira():
    result = get_lados_for_objects(["geladeira"])
    assert len(result) == 1
    entry = result[0]
    assert entry["frente"] == "porta"


def test_get_lados_for_objects_empty_input_returns_empty_list():
    result = get_lados_for_objects([])
    assert result == []


def test_get_lados_for_objects_multiple_objects_returns_all_with_aliases():
    result = get_lados_for_objects(["cama", "geladeira", "criado-mudo"])
    names = {entry["nome"] for entry in result}
    assert "cama" in names
    assert "geladeira" in names
    assert "criado-mudo" not in names  # sem aliases definidos


def test_get_lados_for_objects_each_entry_has_nome_field():
    result = get_lados_for_objects(["cama", "sofa"])
    for entry in result:
        assert "nome" in entry
