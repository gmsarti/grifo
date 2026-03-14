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
            "project_id": self.project_id,
            "id": str(uuid.uuid4())
        }
        self.vector_store.add_texts(
            texts=[content],
            metadatas=[metadata]
        )

    def delete_history(self):
        """Removes all messages from the current thread history."""
        # Chroma doesn't have a simple 'clear collection' in the LC wrapper easily reachable
        # but we can delete with a match-all filter for this collection since it's scoped by collection_name
        self.vector_store.delete(where={"thread_id": self.thread_id})

    def search_history(self, query: str, k: int = 3) -> str:
        # (existing search_history code...)
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

    async def save_fact(self, user_id: str, fact_key: str, fact_value: str, thread_id: Optional[str] = None):
        """Saves a fact to the store, optionally scoped by thread."""
        namespace = ["memories", user_id]
        if thread_id:
            namespace.append(thread_id)
            
        await self.store.aput(
            namespace=namespace,
            key=fact_key,
            value={"content": fact_value}
        )

    async def list_facts(self, user_id: str, thread_id: Optional[str] = None) -> List[dict]:
        """Lists all facts for a user/thread."""
        namespace = ["memories", user_id]
        if thread_id:
            namespace.append(thread_id)
            
        try:
            results = await self.store.asearch(namespace=namespace, query="")
            return [{"fact": r.value["content"], "key": r.key} for r in results]
        except Exception:
            # Safe fallback if search is not supported or fails
            return []

    async def delete_thread_memory(self, user_id: str, thread_id: str):
        """Clears all facts for a specific thread."""
        namespace = ["memories", user_id, thread_id]
        try:
            results = await self.store.asearch(namespace=namespace, query="")
            if results:
                for r in results:
                    await self.store.adelete(namespace=namespace, key=r.key)
        except Exception:
            pass

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
