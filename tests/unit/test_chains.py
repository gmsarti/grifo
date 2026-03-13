import pytest
from unittest.mock import MagicMock
from app.processing.chains import get_first_responder, get_revisor, DRAFT_INSTRUCTION, REVISE_INSTRUCTION
from app.processing.schemas import AnswerQuestion, ReviseAnswer

def test_get_first_responder():
    mock_llm = MagicMock()
    chain = get_first_responder(mock_llm)
    
    # Verify chain structure (RunnableSequence or similar)
    # The chain is: prompt | llm.bind_tools(...)
    assert chain is not None
    
    # Verify LLM was called with bind_tools
    mock_llm.bind_tools.assert_called_once()
    args, kwargs = mock_llm.bind_tools.call_args
    assert AnswerQuestion in kwargs['tools']
    assert kwargs['tool_choice'] == "AnswerQuestion"

def test_get_revisor():
    mock_llm = MagicMock()
    chain = get_revisor(mock_llm)
    
    assert chain is not None
    
    # Verify LLM was called with bind_tools
    mock_llm.bind_tools.assert_called_once()
    args, kwargs = mock_llm.bind_tools.call_args
    assert ReviseAnswer in kwargs['tools']
    assert kwargs['tool_choice'] == "ReviseAnswer"

def test_chain_prompts():
    mock_llm = MagicMock()
    
    # Test first responder prompt injection
    first_resp = get_first_responder(mock_llm)
    # The partial values are stored in partial_variables
    assert first_resp.first.partial_variables["first_instruction"] == DRAFT_INSTRUCTION
    
    # Test revisor prompt injection
    revisor = get_revisor(mock_llm)
    assert revisor.first.partial_variables["first_instruction"] == REVISE_INSTRUCTION
