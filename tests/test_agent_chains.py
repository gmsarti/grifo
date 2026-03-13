import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from app.processing.chains import (
    get_first_responder,
    get_revisor,
    actor_prompt_template,
)
from app.processing.agent import AgentOrchestrator


def test_actor_prompt_template_partial():
    # Verify time is injected
    prompt = actor_prompt_template.invoke({"messages": [], "first_instruction": "test"})
    # prompt.messages[0].content contains the system message
    system_msg = prompt.messages[0].content
    assert "Current time:" in system_msg
    # Ensure it's not a placeholder
    assert "{time}" not in system_msg


def test_get_first_responder():
    mock_llm = MagicMock()
    chain = get_first_responder(mock_llm)
    # Check that bind_tools was called with AnswerQuestion
    mock_llm.bind_tools.assert_called_once()
    args, kwargs = mock_llm.bind_tools.call_args
    assert "AnswerQuestion" in str(kwargs.get("tools"))


def test_get_revisor():
    mock_llm = MagicMock()
    chain = get_revisor(mock_llm)
    # Check that bind_tools was called with ReviseAnswer
    mock_llm.bind_tools.assert_called_once()
    args, kwargs = mock_llm.bind_tools.call_args
    assert "ReviseAnswer" in str(kwargs.get("tools"))


@pytest.mark.anyio
async def test_orchestrator_initialization():
    orchestrator = AgentOrchestrator()
    assert orchestrator.first_responder is not None
    assert orchestrator.revisor is not None
    assert orchestrator.graph is not None
