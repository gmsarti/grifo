from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
import uuid

class VectorizedMessageHistory:
    """
    Short-term (Conversational) Memory:
    Stores and retrieves relevant message context from the current thread using ChromaDB.
    """
    def __init__(self, project_id: str, thread_id: str):
        self.project_id = project_id
        self.thread_id = thread_id
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = Chroma(
            collection_name=f"history_{project_id}_{thread_id}",
            persist_directory=f"{settings.CHROMA_PERSIST_DIRECTORY}/history/{project_id}",
            embedding_function=self.embeddings
        )

    async def add_message(self, message: BaseMessage):
        """Adds a message to the vectorized history."""
        content = message.content
        if not content:
            return
        
        metadata = {
            "type": message.type,
            "thread_id": self.thread_id,
            "id": str(uuid.uuid4())
        }
        self.vector_store.add_texts(
            texts=[content],
            metadatas=[metadata]
        )

    def search_history(self, query: str, k: int = 3) -> str:
        """Retrieves relevant past messages based on semantic similarity."""
        results = self.vector_store.similarity_search(query, k=k)
        if not results:
            return ""
        
        context = []
        for doc in results:
            prefix = "User: " if doc.metadata.get("type") == "human" else "Assistant: "
            context.append(f"{prefix}{doc.page_content}")
            
        return "\n".join(context)

class StoreMemoryManager:
    """
    Long-term (Cross-session) Memory Utility:
    Helper to manage and search facts/preferences in the LangGraph Store.
    """
    def __init__(self, store):
        self.store = store

    async def save_fact(self, user_id: str, fact_key: str, fact_value: str, metadata: Optional[dict] = None):
        """Saves a fact to the store."""
        await self.store.aput(
            namespace=["memories", user_id],
            key=fact_key,
            value={"content": fact_value, "metadata": metadata or {}}
        )

    async def search_memories(self, user_id: str, query: str, limit: int = 5):
        """
        Performs semantic search over store items.
        Note: Current LangGraph BaseStore implementation for search depends on the backend.
        We expect the store to support search() natively if configured with indexing.
        """
        # namespaces are lists of strings
        return await self.store.asearch(
            namespace=["memories", user_id],
            query=query,
            limit=limit
        )
