from typing import Any

from pydantic import BaseModel, Field


class PadroesExtraidos(BaseModel):
    """Schema para with_structured_output — wrapper da lista de padrões retornada pelo LLM."""

    padroes: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Lista de padrões arquitetônicos extraídos do texto. "
            "Cada item é um objeto JSON com campo 'tipo' ('restricao', 'preferencia' ou 'grid') "
            "seguindo as especificações do prompt. "
            "Retorne lista vazia [] se nenhum padrão for identificado."
        ),
    )


class ExtrairPadroesRequest(BaseModel):
    zona: str = Field(
        description="Nome da zona arquitetônica. Ex: 'quarto', 'sala', 'cozinha', 'banheiro'."
    )
    mobiliario: list[str] = Field(
        description="Nomes dos móveis presentes na zona, selecionados pelo usuário."
    )
    texto: str = Field(
        description="Texto em linguagem natural descrevendo as restrições de arranjo."
    )


class ExtrairPadroesResponse(BaseModel):
    zona: str
    mobiliario_valido: list[str]
    padroes: list[dict[str, Any]]
