"""
Chain de classificação de intenção para o router do agente.

Classifica a mensagem do usuário em:
  - "arq_extract": o usuário está descrevendo restrições de arranjo de móveis.
  - "reflexion": qualquer outra coisa (perguntas gerais, conversas, etc.)

Se for "arq_extract", também extrai zona e mobiliário identificados no texto,
usando o vocabulário hardcoded como referência.
"""

import json
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_fast_model
from app.data.arq_vocabulary import OBJETOS_POR_ZONA, ZONAS

# Resumo do vocabulário para o prompt do router (apenas famílias de nível superior)
_VOCAB_SUMMARY = json.dumps(
    {zona: list(objs.keys()) for zona, objs in OBJETOS_POR_ZONA.items()},
    ensure_ascii=False,
)

# Chaves do JSON ({{ / }}) precisam ser escapadas para o LangChain não as interpretar
# como variáveis de template ao renderizar o ChatPromptTemplate.
_VOCAB_SUMMARY_ESCAPED = _VOCAB_SUMMARY.replace("{", "{{").replace("}", "}}")

_SYSTEM = f"""Você é um classificador de intenções para um assistente de layout arquitetônico residencial.

Zonas válidas: {json.dumps(ZONAS, ensure_ascii=False)}

Famílias de móveis por zona (use SOMENTE estes nomes exatos ao preencher 'mobiliario'):
{_VOCAB_SUMMARY_ESCAPED}

Classifique a mensagem em uma das duas intenções:

"arq_extract" — o usuário está descrevendo restrições de posicionamento ou arranjo de móveis
num ambiente: encostado na parede, circulação, distância mínima/máxima, virado para, paralelo,
projeção ortogonal, dentro de zona, etc.

"reflexion" — qualquer outra coisa: pergunta geral, pedido de explicação, conversa, tema
não relacionado a restrições de layout arquitetônico.

Se a intenção for "arq_extract", extraia também:
- zona: o ambiente identificado no texto (um dos valores válidos acima), ou null se não identificado.
- mobiliario: lista com os nomes exatos de móveis do vocabulário da zona que aparecem no texto.
  Use apenas nomes da tabela acima. Lista vazia se nenhum for identificado explicitamente.
"""


class RouterDecision(BaseModel):
    """Decisão do router sobre como processar a mensagem do usuário."""

    intent: Literal["reflexion", "arq_extract"] = Field(
        description=(
            "'arq_extract' se o usuário descreve restrições de arranjo de móveis. "
            "'reflexion' para qualquer outra pergunta."
        )
    )
    zona: str | None = Field(
        default=None,
        description="Zona arquitetônica identificada no texto, ou null se não identificada.",
    )
    mobiliario: list[str] = Field(
        default_factory=list,
        description=(
            "Nomes exatos de móveis do vocabulário da zona que aparecem no texto. "
            "Lista vazia se nenhum for identificado."
        ),
    )


def get_router_chain():
    """
    Constrói a chain de classificação de intenção.

    Input: {"message": str}
    Output: RouterDecision

    Usa get_fast_model() — classificação não exige capacidade de raciocínio avançado.
    """
    llm = get_fast_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM),
        ("human", "{message}"),
    ])
    # method="function_calling" evita o UserWarning do Pydantic causado pelo
    # modo strict da OpenAI ao serializar o campo 'parsed' do RouterDecision.
    return prompt | llm.with_structured_output(RouterDecision, method="function_calling")
