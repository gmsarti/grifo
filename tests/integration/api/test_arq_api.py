"""
Testes de integração para o endpoint POST /api/v1/arq/extrair.

Validações de vocabulário (422) não invocam o LLM e são testadas sem mock.
O path de sucesso (200) mocka a chain para evitar chamadas à API externa.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.arq_schemas import ExtrairPadroesResponse, PadroesExtraidos


# ── Casos de erro de vocabulário (sem LLM) ────────────────────────────────────


async def test_extrair_padroes_unknown_zona_returns_422(client):
    response = await client.post(
        "/api/v1/arq/extrair",
        json={"zona": "garagem", "mobiliario": ["cama"], "texto": "x"},
    )
    assert response.status_code == 422


async def test_extrair_padroes_mobiliario_not_in_zona_returns_422(client):
    response = await client.post(
        "/api/v1/arq/extrair",
        json={"zona": "banheiro", "mobiliario": ["fogao"], "texto": "x"},
    )
    assert response.status_code == 422


async def test_extrair_padroes_422_detail_mentions_unknown_item(client):
    response = await client.post(
        "/api/v1/arq/extrair",
        json={"zona": "quarto", "mobiliario": ["fogao"], "texto": "x"},
    )
    assert response.status_code == 422
    assert "fogao" in response.text


async def test_extrair_padroes_missing_required_fields_returns_422(client):
    """FastAPI deve rejeitar body sem campos obrigatórios."""
    response = await client.post(
        "/api/v1/arq/extrair",
        json={"zona": "quarto"},  # faltam mobiliario e texto
    )
    assert response.status_code == 422


# ── Caso de sucesso (LLM mockado) ─────────────────────────────────────────────


async def test_extrair_padroes_valid_request_returns_200(client):
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value=PadroesExtraidos(
            padroes=[
                {
                    "tipo": "restricao",
                    "padrao": "encostado",
                    "objeto": {"nome": "cama"},
                    "lado": "fundos",
                }
            ]
        )
    )

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        response = await client.post(
            "/api/v1/arq/extrair",
            json={
                "zona": "quarto",
                "mobiliario": ["cama", "guarda-roupa"],
                "texto": "A cama deve estar encostada na parede dos fundos",
            },
        )

    assert response.status_code == 200


async def test_extrair_padroes_response_contains_expected_fields(client):
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PadroesExtraidos(padroes=[]))

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        response = await client.post(
            "/api/v1/arq/extrair",
            json={"zona": "quarto", "mobiliario": ["cama"], "texto": "x"},
        )

    body = response.json()
    assert "zona" in body
    assert "mobiliario_valido" in body
    assert "padroes" in body


async def test_extrair_padroes_response_zona_matches_request(client):
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PadroesExtraidos(padroes=[]))

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        response = await client.post(
            "/api/v1/arq/extrair",
            json={"zona": "sala", "mobiliario": ["sofa"], "texto": "x"},
        )

    assert response.json()["zona"] == "sala"


async def test_extrair_padroes_empty_text_returns_empty_padroes(client):
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PadroesExtraidos(padroes=[]))

    with patch("app.services.arq_service._get_chain", return_value=mock_chain):
        response = await client.post(
            "/api/v1/arq/extrair",
            json={"zona": "quarto", "mobiliario": ["cama"], "texto": ""},
        )

    assert response.status_code == 200
    assert response.json()["padroes"] == []
