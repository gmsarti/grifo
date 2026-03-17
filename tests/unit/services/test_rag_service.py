from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_rag_service_chat_flow():
    """
    Detailed:
    - Given a session_id and a question
    - When service.chat is called
    - Then it should:
        1. Get project_id from session.
        2. Call RAG engine.
        3. Save user message.
        4. Save assistant response.
        5. Return the response.
    """
    from app.models.chat import Session
    from app.services.rag_service import RAGService

    # Mocks
    mock_chat_repo = MagicMock()
    mock_rag_controller = MagicMock()

    # Mock session retrieval
    mock_session = Session(id=1, project_id=10)
    mock_chat_repo.get_session_by_id = AsyncMock(return_value=mock_session)
    mock_chat_repo.add_message = AsyncMock()

    # Mock RAG engine response
    mock_rag_controller.invoke = AsyncMock(
        return_value={"generation": "The answer is 42", "documents": []}
    )

    service = RAGService(mock_chat_repo, mock_rag_controller)
    response = await service.chat(session_id=1, question="What is the answer?")

    assert response == "The answer is 42"

    # Verify calls
    mock_chat_repo.get_session_by_id.assert_called_once_with(1)
    mock_rag_controller.invoke.assert_called_once_with(
        "What is the answer?", project_id="10"
    )

    # Verify two messages were saved (user and assistant)
    assert mock_chat_repo.add_message.call_count == 2
