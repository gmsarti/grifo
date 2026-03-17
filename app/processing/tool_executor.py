from langchain_core.tools import StructuredTool
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode

from app.core.config import settings
from app.core.llm import get_fast_model
from app.data_source.vector_store import VectorStoreManager
from app.schemas.agent_schemas import AnswerQuestion, ReviseAnswer

# Connectors & Tools
# Usamos "Lazy Loading" (carregamento sob demanda) para que as ferramentas sejam
# instanciadas apenas no momento da execução. Isso evita erros de validação
# de chaves de API durante o carregamento do módulo (import time),
# o que é essencial para que os testes unitários rodem em ambientes de CI.

_grader_llm = None


def get_grader_llm():
    """Retorna o LLM de avaliação de forma preguiçosa (lazy)."""
    global _grader_llm
    if _grader_llm is None:
        _grader_llm = get_fast_model()
    return _grader_llm


def get_tavily_tool():
    """Instancia o TavilySearch apenas quando necessário."""
    tavily_kwargs = {"max_results": 3}
    if settings.TAVILY_API_KEY:
        tavily_kwargs["tavily_api_key"] = settings.TAVILY_API_KEY
    return TavilySearch(**tavily_kwargs)


async def run_queries(search_queries: list[str], **kwargs):
    """
    Run hybrid search with CRAG fallback.
    1. Search local Vector Store (Hybrid).
    2. If docs are missing or graded irrelevant, search Tavily.
    """
    results = []
    vector_db = VectorStoreManager()
    tavily_tool = get_tavily_tool()

    for query in search_queries:
        # 1. Search Vector Store
        docs = vector_db.search_hybrid(query, k=3)
        context = ""

        if docs:
            # 2. Grade documents
            relevant_docs = []
            for doc in docs:
                is_relevant = await grade_document_relevance(query, doc.page_content)
                if is_relevant:
                    relevant_docs.append(doc.page_content)

            if relevant_docs:
                context = "\n\n".join(relevant_docs)

        # 3. Fallback to Tavily if context is empty
        if not context:
            web_results = await tavily_tool.ainvoke({"query": query})
            context = str(web_results)

        results.append(context)

    return "\n---\n".join(results)


async def grade_document_relevance(query: str, document_content: str) -> bool:
    """Uses a fast model to grade document relevance (simple binary check)."""
    prompt = f"""Evaluate if the following document is relevant to the query:
Query: {query}
Document: {document_content}

Respond only with 'YES' or 'NO'."""
    try:
        grader_llm = get_grader_llm()
        response = await grader_llm.ainvoke(prompt)
        return "YES" in response.content.upper()
    except Exception:
        return True  # Fallback to relevant if error


execute_tools = ToolNode(
    tools=[
        StructuredTool.from_function(run_queries, name=AnswerQuestion.__name__),
        StructuredTool.from_function(run_queries, name=ReviseAnswer.__name__),
    ]
)
