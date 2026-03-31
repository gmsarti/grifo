"""
Chain de extração de padrões arquitetônicos.

Carrega o prompt de app/prompts/extrator_padroes_arq.md em tempo de import
(falha rápido se o arquivo estiver ausente) e expõe duas funções públicas:

  render_arq_prompt(objetos, lados, zonas, texto) -> str
      Substitui as 4 variáveis $-prefixadas no template e devolve o prompt
      completamente renderizado.

  get_arq_extractor_chain() -> Runnable
      Constrói e devolve a chain LangChain. Input: {"prompt_text": str}.
      Output: PadroesExtraidos (via with_structured_output).
"""

import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_reasoner
from app.schemas.arq_schemas import PadroesExtraidos

# Carregado uma única vez na inicialização do módulo.
# Se o arquivo não existir, a aplicação falha na importação — comportamento intencional.
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extrator_padroes_arq.md"
_PROMPT_TEMPLATE: str = _PROMPT_PATH.read_text(encoding="utf-8")


def render_arq_prompt(
    objetos: dict,
    lados: list[dict],
    zonas: list[str],
    texto: str,
) -> str:
    """
    Substitui as 4 variáveis $-prefixadas no template do extrator.

    A substituição usa str.replace porque o sigilo `$` não é suportado
    nativamente pelos formatos de template do LangChain (f-string ou mustache).
    As variáveis têm nomes únicos, então a ordem das substituições não importa.
    """
    rendered = _PROMPT_TEMPLATE
    rendered = rendered.replace("$objetos", json.dumps(objetos, ensure_ascii=False, indent=2))
    rendered = rendered.replace("$lados", json.dumps(lados, ensure_ascii=False))
    rendered = rendered.replace("$zonas", json.dumps(zonas, ensure_ascii=False))
    rendered = rendered.replace("$texto", texto)
    return rendered


def get_arq_extractor_chain():
    """
    Constrói a chain de extração de padrões arquitetônicos.

    Input esperado: {"prompt_text": str}  (prompt já renderizado pelo serviço)
    Output: PadroesExtraidos

    Usa get_reasoner() porque extração estruturada de múltiplos padrões com
    gramática complexa se beneficia do modelo de maior capacidade de raciocínio.
    """
    llm = get_reasoner()
    prompt = ChatPromptTemplate.from_messages([
        ("human", "{prompt_text}"),
    ])
    # method="function_calling" porque PadroesExtraidos usa list[dict[str, Any]],
    # que não é suportado pelo modo strict JSON schema da OpenAI.
    return prompt | llm.with_structured_output(PadroesExtraidos, method="function_calling")
