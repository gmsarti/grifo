import pytest
import json
import logging
from io import StringIO
from app.core.logging import get_logger, timed_process, JsonFormatter
from app.processing.agent import AgentOrchestrator
from unittest.mock import patch, MagicMock, AsyncMock

def test_json_formatter():
    formatter = JsonFormatter()
    # Create a dummy log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=None,
        exc_info=None
    )
    record.metadata = {"key": "value"}
    record.duration = 1.23
    
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["message"] == "Test message"
    assert data["level"] == "INFO"
    assert data["metadata"] == {"key": "value"}
    assert data["duration_seconds"] == 1.23

def test_timed_process_logging():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    
    logger = logging.getLogger("test_timed")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    with timed_process("my_process", logger=logger, metadata={"p": 1}):
        pass
        
    output = stream.getvalue().strip().split("\n")
    assert len(output) == 2
    
    start_log = json.loads(output[0])
    assert "Starting process: my_process" in start_log["message"]
    assert start_log["metadata"] == {"p": 1}
    
    end_log = json.loads(output[1])
    assert "Finished process: my_process" in end_log["message"]
    assert "duration_seconds" in end_log

@pytest.mark.asyncio
async def test_agent_process_message_metadata():
    with patch("app.processing.agent.VectorizedMessageHistory") as mock_hist_class, \
         patch("app.processing.agent.get_openai_callback") as mock_cb:
        
        # Correctly mock the instance methods
        mock_hist_instance = mock_hist_class.return_value
        mock_hist_instance.add_message = AsyncMock()
        
        # Mock callback behavior
        mock_cb_instance = MagicMock()
        mock_cb_instance.total_tokens = 100
        mock_cb_instance.prompt_tokens = 50
        mock_cb_instance.completion_tokens = 50
        mock_cb_instance.total_cost = 0.01
        mock_cb.return_value.__enter__.return_value = mock_cb_instance
        
        orchestrator = AgentOrchestrator()
        
        with patch.object(orchestrator.graph, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            from langchain_core.messages import AIMessage
            mock_invoke.return_value = {"messages": [AIMessage(content="Hello")]}
            
            await orchestrator.process_message(
                "hi", 
                thread_id="t1", 
                user_id="u1", 
                project_id="p1"
            )
            
            mock_invoke.assert_called_once()
            _, kwargs = mock_invoke.call_args
            assert kwargs["config"]["metadata"]["thread_id"] == "t1"
            assert kwargs["config"]["metadata"]["user_id"] == "u1"
            assert kwargs["config"]["metadata"]["project_id"] == "p1"
            assert kwargs["config"]["configurable"]["project_id"] == "p1"
