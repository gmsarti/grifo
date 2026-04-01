from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.arq_schemas import (
    ExtrairPadroesRequest,
    ExtrairPadroesResponse,
    PadroesExtraidos,
)
from app.services.arq_service import ArqService, _filter_objetos, _strip_errors


# ── _filter_objetos ───────────────────────────────────────────────────────────


def test_filter_objetos_raises_422_for_unknown_zona():
    with pytest.raises(HTTPException) as exc_info:
        _filter_objetos("garagem", ["cama"])
    assert exc_info.value.status_code == 422


def test_filter_objetos_raises_422_for_mobiliario_not_in_zona():
    with pytest.raises(HTTPException) as exc_info:
        _filter_objetos("banheiro", ["fogao"])
    assert exc_info.value.status_code == 422
    assert "fogao" in str(exc_info.value.detail)


def test_filter_objetos_raises_422_error_lists_all_unknown_items():
    with pytest.raises(HTTPException) as exc_info:
        _filter_objetos("quarto", ["cama", "fogao", "sofa"])
    detail = str(exc_info.value.detail)
    assert "fogao" in detail
    assert "sofa" in detail


def test_filter_objetos_returns_filtered_dict_for_valid_top_level_family():
    result = _filter_objetos("quarto", ["cama"])
    assert "cama" in result


def test_filter_objetos_returns_only_requested_families():
    result = _filter_objetos("quarto", ["cama"])
    assert "guarda-roupa" not in result
    assert "escrivaninha" not in result


def test_filter_objetos_returns_multiple_requested_families():
    result = _filter_objetos("quarto", ["cama", "criado-mudo"])
    assert "cama" in result
    assert "criado-mudo" in result


def test_filter_objetos_preserves_leaf_values_of_family():
    result = _filter_objetos("quarto", ["cama"])
    assert result["cama"] == ["solteiro", "casal", "queen", "king"]


# ── _strip_errors ─────────────────────────────────────────────────────────────


def test_strip_errors_empty_list_returns_empty_valid_and_empty_errors():
    valid, errors = _strip_errors([])
    assert valid == []
    assert errors == []


def test_strip_errors_all_valid_patterns_returns_all_in_valid():
    patterns = [
        {"tipo": "restricao", "padrao": "encostado"},
        {"tipo": "preferencia", "padrao": "preferencia_escolha"},
    ]
    valid, errors = _strip_errors(patterns)
    assert len(valid) == 2
    assert errors == []


def test_strip_errors_separates_error_objects_from_valid_patterns():
    patterns = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}},
        {"erro": "objeto_desconhecido", "texto": "sofá"},
    ]
    valid, errors = _strip_errors(patterns)
    assert len(valid) == 1
    assert len(errors) == 1
    assert valid[0]["padrao"] == "encostado"
    assert errors[0]["erro"] == "objeto_desconhecido"


def test_strip_errors_all_error_objects_returns_empty_valid():
    patterns = [
        {"erro": "objeto_desconhecido", "texto": "sofá"},
        {"erro": "lado_desconhecido", "texto": "topo"},
    ]
    valid, errors = _strip_errors(patterns)
    assert valid == []
    assert len(errors) == 2


# ── ArqService.extrair_padroes ────────────────────────────────────────────────


async def test_extrair_padroes_returns_correct_zona_in_response():
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value=PadroesExtraidos(padroes=[])
    )

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        service = ArqService()
        request = ExtrairPadroesRequest(zona="quarto", mobiliario=["cama"], texto="x")
        result = await service.extrair_padroes(request)

    assert result.zona == "quarto"


async def test_extrair_padroes_returns_mobiliario_valido():
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PadroesExtraidos(padroes=[]))

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        service = ArqService()
        request = ExtrairPadroesRequest(
            zona="quarto", mobiliario=["cama", "criado-mudo"], texto="x"
        )
        result = await service.extrair_padroes(request)

    assert result.mobiliario_valido == ["cama", "criado-mudo"]


async def test_extrair_padroes_returns_texto_resumo():
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PadroesExtraidos(padroes=[]))

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        service = ArqService()
        request = ExtrairPadroesRequest(zona="quarto", mobiliario=["cama"], texto="x")
        result = await service.extrair_padroes(request)

    assert isinstance(result.texto_resumo, str)
    assert len(result.texto_resumo) > 0


async def test_extrair_padroes_texto_resumo_reflects_patterns():
    padroes = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"}
    ]
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PadroesExtraidos(padroes=padroes))

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        service = ArqService()
        request = ExtrairPadroesRequest(zona="quarto", mobiliario=["cama"], texto="x")
        result = await service.extrair_padroes(request)

    assert "cama" in result.texto_resumo
    assert "encostado" in result.texto_resumo


async def test_extrair_padroes_passes_rendered_prompt_to_chain():
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PadroesExtraidos(padroes=[]))

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        service = ArqService()
        texto = "A cama deve estar encostada na cabeceira"
        request = ExtrairPadroesRequest(zona="quarto", mobiliario=["cama"], texto=texto)
        await service.extrair_padroes(request)

    call_args = mock_chain.ainvoke.call_args
    prompt_text = call_args.args[0]["prompt_text"] if call_args.args else call_args.kwargs["prompt_text"]  # noqa: E501
    assert texto in prompt_text


async def test_extrair_padroes_strips_error_objects_from_response():
    patterns_with_error = [
        {"tipo": "restricao", "padrao": "encostado", "objeto": {"nome": "cama"}, "lado": "fundos"},
        {"erro": "objeto_desconhecido", "texto": "sofá"},
    ]
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value=PadroesExtraidos(padroes=patterns_with_error)
    )

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        service = ArqService()
        request = ExtrairPadroesRequest(zona="quarto", mobiliario=["cama"], texto="x")
        result = await service.extrair_padroes(request)

    assert len(result.padroes) == 1
    assert result.padroes[0]["padrao"] == "encostado"


async def test_extrair_padroes_raises_422_when_zona_is_invalid():
    service = ArqService()
    request = ExtrairPadroesRequest(zona="garagem", mobiliario=["cama"], texto="x")

    with pytest.raises(HTTPException) as exc_info:
        await service.extrair_padroes(request)

    assert exc_info.value.status_code == 422


async def test_extrair_padroes_raises_422_when_mobiliario_not_in_zona():
    service = ArqService()
    request = ExtrairPadroesRequest(
        zona="banheiro", mobiliario=["fogao"], texto="x"
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.extrair_padroes(request)

    assert exc_info.value.status_code == 422
