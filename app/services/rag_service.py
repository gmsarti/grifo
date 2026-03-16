from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import MessageCreate
from app.services.rag_service_facade import AgenticRAGController


class RAGService:
    def __init__(self, chat_repo: ChatRepository, rag_controller: AgenticRAGController):
        self.chat_repo = chat_repo
        self.rag_controller = rag_controller

    async def chat(self, session_id: int, question: str) -> str:
        # 1. Get session to find project_id
        session = await self.chat_repo.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 2. Save user message
        await self.chat_repo.add_message(
            session_id, MessageCreate(role="user", content=question)
        )

        # 3. Call RAG engine
        result = await self.rag_controller.invoke(
            question, project_id=str(session.project_id)
        )
        answer = result.get("generation", "Error generating response")

        # 4. Save assistant message
        await self.chat_repo.add_message(
            session_id, MessageCreate(role="assistant", content=answer)
        )

        return answer
