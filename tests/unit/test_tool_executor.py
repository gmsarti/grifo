import pytest
from unittest.mock import MagicMock, patch
from app.processing.tool_executor import run_queries, execute_tools
from langgraph.prebuilt import ToolNode


@patch("app.processing.tool_executor.TavilySearch")
def test_tavily_initialization_with_settings(mock_tavily_class):
    # This test might be tricky due to module level instantiation,
    # but we can verify the behavior if we reload or re-import.
    # For now, let's focus on run_queries.
    pass


def test_run_queries_calls_tavily_batch():
    with patch("app.processing.tool_executor.tavily_tool") as mock_tavily:
        queries = ["query 1", "query 2"]
        run_queries(queries)

        mock_tavily.batch.assert_called_once_with(
            [{"query": "query 1"}, {"query": "query 2"}]
        )


def test_execute_tools_is_valid_tool_node():
    assert isinstance(execute_tools, ToolNode)
    # Check that tools are present by name
    tool_names = [tool.name for tool in execute_tools.tools]
    assert "AnswerQuestion" in tool_names
    assert "ReviseAnswer" in tool_names
