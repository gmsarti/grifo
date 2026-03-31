from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.arq_schemas import ExtrairPadroesRequest, ExtrairPadroesResponse
from app.services.arq_service import arq_service

logger = get_logger(__name__)

router = APIRouter()


@router.post("/extrair", response_model=ExtrairPadroesResponse)
async def extrair_padroes(body: ExtrairPadroesRequest) -> ExtrairPadroesResponse:
    """
    Extrai padrões arquitetônicos de um texto descritivo de arranjo de mobiliário.

    Valida o mobiliário informado contra o vocabulário da zona antes de invocar o LLM.
    Retorna `padroes: []` se nenhum padrão for identificado no texto.
    """
    try:
        return await arq_service.extrair_padroes(body)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("arq_extractor: erro inesperado")
        raise HTTPException(status_code=500, detail=str(e))
