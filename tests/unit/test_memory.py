import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from app.processing.memory import VectorizedMessageHistory, StoreMemoryManager
from langgraph.store.memory import InMemoryStore

@pytest.mark.asyncio
async def test_vectorized_history_add_and_search():
    thread_id = "test_thread_123"
    
    with patch("app.processing.memory.Chroma") as mock_chroma, \
         patch("app.processing.memory.OpenAIEmbeddings") as mock_embeddings:
        
        history = VectorizedMessageHistory(thread_id)
        mock_vs = mock_chroma.return_value
        
        # Test add_message
        msg = HumanMessage(content="Hello world")
        await history.add_message(msg)
        mock_vs.add_texts.assert_called_once()
        
        # Test search_history
        mock_vs.similarity_search.return_value = [
            MagicMock(page_content="Hello world", metadata={"type": "human"})
        ]
        res = history.search_history("hello")
        assert "User: Hello world" in res

@pytest.mark.asyncio
async def test_store_memory_manager():
    mock_store = AsyncMock(spec=InMemoryStore)
    manager = StoreMemoryManager(mock_store)
    
    # Test save_fact
    await manager.save_fact("user1", "pref", "likes coffee")
    mock_store.aput.assert_called_once()
    args, kwargs = mock_store.aput.call_args
    assert kwargs["namespace"] == ["memories", "user1"]
    assert kwargs["key"] == "pref"
    assert kwargs["value"]["content"] == "likes coffee"

    # Test search_memories
    mock_store.asearch.return_value = [
        MagicMock(value={"content": "likes coffee"})
    ]
    res = await manager.search_memories("user1", "coffee")
    assert len(res) == 1
    assert res[0].value["content"] == "likes coffee"
