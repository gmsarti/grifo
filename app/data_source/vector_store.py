from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


class VectorStoreManager:
    """
    Data Source Layer: Responsável pela ligação ao ChromaDB (RAG).
    """

    def __init__(self):
        # Nota: Mesmo usando DeepSeek para o LLM, é comum usar OpenAI para embeddings
        # pois são baratos e de alta qualidade.
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings,
        )

    def search_context(self, query: str, k: int = 3) -> str:
        """Busca os documentos mais relevantes na base vetorial."""
        docs = self.vector_store.similarity_search(query, k=k)
        if not docs:
            return "Nenhuma informação encontrada na base de conhecimento."
        return "\n\n".join([doc.page_content for doc in docs])
