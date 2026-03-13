from langchain_tavily import TavilySearch
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode
from app.core.config import settings
from app.processing.schemas import AnswerQuestion, ReviseAnswer

# Only pass api_key if explicitly set in settings, otherwise let it fall back to env vars
tavily_kwargs = {"max_results": 3}
if settings.TAVILY_API_KEY:
    tavily_kwargs["api_key"] = settings.TAVILY_API_KEY

tavily_tool = TavilySearch(**tavily_kwargs)


def run_queries(search_queries: list[str], **kwargs):
    """Run the generated queries."""
    return tavily_tool.batch([{"query": query} for query in search_queries])


execute_tools = ToolNode(
    tools=[
        StructuredTool.from_function(run_queries, name=AnswerQuestion.__name__),
        StructuredTool.from_function(run_queries, name=ReviseAnswer.__name__),
    ]
)
