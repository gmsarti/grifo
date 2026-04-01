"""
Serviço de extração de padrões arquitetônicos.

Responsabilidades:
  - Validar a zona e o mobiliário selecionado contra o vocabulário da zona.
  - Filtrar o catálogo de objetos para incluir apenas o mobiliário presente.
  - Montar os lados alternativos para os objetos selecionados.
  - Renderizar o prompt e invocar a chain de extração.
  - Separar os error-objects retornados pelo LLM dos padrões válidos.
"""

from typing import Any

from fastapi import HTTPException

from app.core.logging import get_logger
from app.data.arq_vocabulary import (
    OBJETOS_POR_ZONA,
    ZONAS,
    get_lados_for_objects,
)
from app.processing.arq_chain import get_arq_extractor_chain, render_arq_prompt
from app.processing.arq_text_converter import padroes_para_texto
from app.schemas.arq_schemas import ExtrairPadroesRequest, ExtrairPadroesResponse

logger = get_logger(__name__)

# Singleton lazy — a chain é stateless e cara de construir (instancia o LLM).
_arq_chain = None


def _get_chain():
    global _arq_chain
    if _arq_chain is None:
        _arq_chain = get_arq_extractor_chain()
    return _arq_chain


def _filter_objetos(zona: str, mobiliario: list[str]) -> dict:
    """
    Filtra o catálogo completo da zona para incluir apenas os móveis selecionados.

    Busca cada nome em três lugares do catálogo:
      1. Chave de família de nível superior (ex: "cama")
      2. Chave de subfamília dentro de uma família (ex: "guarda-roupa" dentro de algum grupo)
      3. Folha dentro de uma lista de valores (ex: "solteiro" dentro de "cama")

    Levanta HTTPException(422) se a zona for inválida ou se algum nome não for
    encontrado no catálogo da zona.
    """
    if zona not in ZONAS:
        raise HTTPException(
            status_code=422,
            detail=f"Zona '{zona}' não reconhecida. Zonas válidas: {ZONAS}",
        )

    full_catalog = OBJETOS_POR_ZONA[zona]
    filtered: dict = {}
    unknown: list[str] = []

    for name in mobiliario:
        if name in full_catalog:
            # Chave de família de nível superior
            filtered[name] = full_catalog[name]
            continue

        found = False
        for family_key, family_val in full_catalog.items():
            if isinstance(family_val, dict) and name in family_val:
                # Chave de subfamília
                if family_key not in filtered:
                    filtered[family_key] = {}
                filtered[family_key][name] = family_val[name]
                found = True
                break
            if isinstance(family_val, list) and name in family_val:
                # Folha dentro de uma lista
                if family_key not in filtered:
                    filtered[family_key] = []
                if isinstance(filtered[family_key], list):
                    filtered[family_key].append(name)
                found = True
                break

        if not found:
            unknown.append(name)

    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Mobiliário não encontrado na zona '{zona}': {unknown}",
        )

    return filtered


def _strip_errors(
    raw_patterns: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Separa os padrões válidos dos error-objects que o LLM pode retornar.

    O prompt instrui o LLM a retornar {"erro": "objeto_desconhecido", "texto": "..."}
    quando um termo no texto não corresponde a nenhuma entrada do vocabulário.
    Esses objetos são separados e logados como warnings, não devolvidos ao cliente.
    """
    errors = [p for p in raw_patterns if "erro" in p]
    valid = [p for p in raw_patterns if "erro" not in p]
    return valid, errors


class ArqService:
    """
    Facade stateless para o pipeline de extração de padrões arquitetônicos.
    Seguro para uso como singleton em nível de módulo.
    """

    async def extrair_padroes(
        self, request: ExtrairPadroesRequest
    ) -> ExtrairPadroesResponse:
        # 1. Valida zona e filtra objetos para o mobiliário selecionado
        objetos_filtrados = _filter_objetos(request.zona, request.mobiliario)

        # 2. Monta lados alternativos apenas para os móveis presentes
        lados = get_lados_for_objects(request.mobiliario)

        # 3. Renderiza o prompt com os vocabulários filtrados
        prompt_text = render_arq_prompt(
            objetos=objetos_filtrados,
            lados=lados,
            zonas=ZONAS,
            texto=request.texto,
        )

        # 4. Invoca o LLM via chain
        chain = _get_chain()
        result = await chain.ainvoke({"prompt_text": prompt_text})

        # 5. Filtra error-objects e loga como warning
        valid_patterns, error_objects = _strip_errors(result.padroes)
        if error_objects:
            logger.warning(
                "arq_extractor: LLM retornou %d error-object(s) — termos não reconhecidos no vocabulário",
                len(error_objects),
                extra={
                    "metadata": {
                        "zona": request.zona,
                        "error_objects": error_objects,
                    }
                },
            )

        return ExtrairPadroesResponse(
            zona=request.zona,
            mobiliario_valido=request.mobiliario,
            padroes=valid_patterns,
            texto_resumo=padroes_para_texto(valid_patterns),
        )


# Singleton de módulo — sem estado, sem custo de inicialização.
arq_service = ArqService()
