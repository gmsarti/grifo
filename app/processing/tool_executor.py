from langchain_tavily import TavilySearch
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode
from app.core.config import settings
from app.core.llm import get_fast_model
from app.processing.schemas import AnswerQuestion, ReviseAnswer
from app.data_source.vector_store import VectorStoreManager

# Connectors
vector_db = VectorStoreManager()
tavily_kwargs = {"max_results": 3}
if settings.TAVILY_API_KEY:
    tavily_kwargs["api_key"] = settings.TAVILY_API_KEY
tavily_tool = TavilySearch(**tavily_kwargs)

# Grader LLM
grader_llm = get_fast_model()

async def grade_document_relevance(query: str, document_content: str) -> bool:
    """Uses a fast model to grade document relevance (simple binary check)."""
    prompt = f"""Evaluate if the following document is relevant to the query:
Query: {query}
Document: {document_content}

Respond only with 'YES' or 'NO'."""
    try:
        response = await grader_llm.ainvoke(prompt)
        return "YES" in response.content.upper()
    except Exception:
        return True  # Fallback to relevant if error

async def run_queries(search_queries: list[str], **kwargs):
    """
    Run hybrid search with CRAG fallback.
    1. Search local Vector Store (Hybrid).
    2. If docs are missing or graded irrelevant, search Tavily.
    """
    results = []
    
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


execute_tools = ToolNode(
    tools=[
        StructuredTool.from_function(run_queries, name=AnswerQuestion.__name__),
        StructuredTool.from_function(run_queries, name=ReviseAnswer.__name__),
    ]
)
