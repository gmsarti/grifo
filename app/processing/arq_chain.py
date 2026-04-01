"""
Chain de extração de padrões arquitetônicos.

Carrega o prompt de app/prompts/extrator_padroes_arq_v2.md em tempo de import
(falha rápido se o arquivo estiver ausente) e expõe duas funções públicas:

  render_arq_prompt(objetos, lados, zonas, texto) -> str
      Substitui as 4 variáveis $-prefixadas no template e devolve o prompt
      completamente renderizado.

  get_arq_extractor_chain() -> Runnable
      Constrói e devolve a chain LangChain. Input: {"prompt_text": str}.
      Output: PadroesExtraidos (via parser JSON customizado).
"""

import json
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_reasoner
from app.schemas.arq_schemas import PadroesExtraidos

# Carregado uma única vez na inicialização do módulo.
# Se o arquivo não existir, a aplicação falha na importação — comportamento intencional.
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extrator_padroes_arq_v2.md"
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


def _parse_padroes(text: str) -> PadroesExtraidos:
    """
    Converte a saída de texto livre do LLM em PadroesExtraidos.

    O prompt instrui o LLM a retornar uma lista JSON pura (ex: [{...}, {...}]).
    with_structured_output(method="function_calling") é incompatível com esse
    formato porque espera que o LLM chame uma função, não que escreva JSON diretamente.
    Este parser resolve o conflito sem modificar o prompt.
    """
    text = text.strip()
    # Remove bloco de código Markdown se o modelo incluir ```json ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    padroes = json.loads(text)
    return PadroesExtraidos(padroes=padroes)


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
    return prompt | llm | StrOutputParser() | _parse_padroes
