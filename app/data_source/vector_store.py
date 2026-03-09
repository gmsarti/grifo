from typing import List
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.core.config import settings
from app.data_source.loaders import FileIngestionService, WebIngestionService


class VectorStoreManager:
    """
    Data Source Layer: Responsável pela ligação ao ChromaDB (RAG) e Ingestão.
    """

    def __init__(self):
        # Nota: Mesmo usando DeepSeek para o LLM, é comum usar OpenAI para embeddings
        # pois são baratos e de alta qualidade.
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings,
        )
        self.file_service = FileIngestionService()
        self.web_service = WebIngestionService()
        self.bm25_retriever = None
        self._all_documents = []  # Keep track of documents for BM25 re-initialization

    def search_context(self, query: str, k: int = 3) -> str:
        """Busca os documentos mais relevantes na base vetorial."""
        docs = self.vector_store.similarity_search(query, k=k)
        if not docs:
            return "Nenhuma informação encontrada na base de conhecimento."
        return "\n\n".join([doc.page_content for doc in docs])

    def search_bm25(self, query: str, k: int = 3) -> List[Document]:
        """Busca documentos usando BM25 (palavras-chave)."""
        if not self.bm25_retriever:
            return []
        return self.bm25_retriever.invoke(query, k=k)

    def add_documents(self, documents: List[Document]):
        """Adiciona uma lista de documentos ao banco vetorial e atualiza o BM25."""
        self.vector_store.add_documents(documents)
        self._all_documents.extend(documents)

        # O BM25Retriever do LangChain não suporta adição incremental nativamente
        # de forma persistente e simples, então reinicializamos com todos os docs.
        # Em produção com muitos docs, isso deve ser otimizado (TASK-16).
        from langchain_community.retrievers import BM25Retriever

        if self._all_documents:
            self.bm25_retriever = BM25Retriever.from_documents(self._all_documents)

    def ingest_file(self, file_path: str):
        """Processa um arquivo e adiciona ao banco vetorial."""
        documents = self.file_service.process_file(file_path)
        self.add_documents(documents)

    def ingest_url(self, url: str):
        """Processa uma URL e adiciona ao banco vetorial."""
        documents = self.web_service.process_url(url)
        self.add_documents(documents)
