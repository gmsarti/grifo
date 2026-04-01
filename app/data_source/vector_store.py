import asyncio
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma  # Oficial para LangChain/Chroma integration
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings
from pydantic import ConfigDict

from app.core.config import settings
from app.core.logging import get_logger
from app.data_source.loaders import FileIngestionService, WebIngestionService

logger = get_logger(__name__)


class HybridRetriever(BaseRetriever):
    """
    Custom Retriever that combines Vector Search and BM25 using
    Reciprocal Rank Fusion (RRF).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vector_retriever: Any
    bm25_retriever: Any
    k: int = 4

    def _get_relevant_documents(
        self, query: str, *, run_manager=None
    ) -> list[Document]:
        # Perform searches in both retrievers
        vec_docs = self.vector_retriever.invoke(query)
        bm25_docs = self.bm25_retriever.invoke(query)

        # Rank fusion (RRF)
        all_docs = {}

        # Simple ID or content hashing if id is missing
        def get_doc_id(doc):
            return doc.metadata.get("id") or hash(doc.page_content)

        for rank, doc in enumerate(vec_docs, 1):
            doc_id = get_doc_id(doc)
            all_docs[doc_id] = (1 / (60 + rank), doc)

        for rank, doc in enumerate(bm25_docs, 1):
            doc_id = get_doc_id(doc)
            if doc_id in all_docs:
                v_score, _ = all_docs[doc_id]
                all_docs[doc_id] = (v_score + 1 / (60 + rank), doc)
            else:
                all_docs[doc_id] = (1 / (60 + rank), doc)

        # Sort by combined score (score is the first element of the tuple)
        sorted_pairs = sorted(all_docs.values(), key=lambda x: x[0], reverse=True)
        return [doc for score, doc in sorted_pairs][: self.k]


class VectorStoreManager:
    """
    Data Source Layer: Responsável pela ligação ao ChromaDB (RAG) e Ingestão.
    """

    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = Chroma(
            collection_name=f"project_{project_id}",
            persist_directory=f"{settings.CHROMA_PERSIST_DIRECTORY}/{project_id}",
            embedding_function=self.embeddings,
        )
        self.file_service = FileIngestionService()
        self.web_service = WebIngestionService()
        self.bm25_retriever = None
        self.hybrid_retriever = None  # replaced ensemble
        self._all_documents = []  # Track all docs for BM25 updates
        # B-027: lock para proteger mutações concorrentes em _all_documents e BM25
        self._lock = asyncio.Lock()
        self._rebuild_bm25_from_chroma()

    def _rebuild_bm25_from_chroma(self):
        """Reconstrói o índice BM25 e o HybridRetriever a partir dos documentos já persistidos no ChromaDB."""
        result = self.vector_store.get(include=["documents", "metadatas"])
        texts = result.get("documents") or []
        metadatas = result.get("metadatas") or [{}] * len(texts)

        docs = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(texts, metadatas)
        ]
        if not docs:
            return

        self._all_documents = docs
        self._rebuild_bm25()

    def _rebuild_bm25(self):
        """Reconstrói o índice BM25 e o HybridRetriever a partir de self._all_documents."""
        # B-028: método extraído para reutilização em add_documents e delete_document
        if not self._all_documents:
            self.bm25_retriever = None
            self.hybrid_retriever = None
            return
        self.bm25_retriever = BM25Retriever.from_documents(self._all_documents, k=5)
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            bm25_retriever=self.bm25_retriever,
            k=5,
        )

    def search(
        self, query: str, search_type: str = "hybrid", k: int = 3
    ) -> list[Document]:
        """
        Unified search interface for the agent.
        Available types: 'hybrid', 'vector', 'bm25'.
        Defaults to 'hybrid'.
        """
        if search_type == "vector":
            return self.vector_store.similarity_search(query, k=k)
        elif search_type == "bm25":
            return self.search_bm25(query, k=k)
        else:
            # Default to hybrid
            return self.search_hybrid(query, k=k)

    def search_context(self, query: str, k: int = 3) -> str:
        """Busca semântica pura via vector store."""
        docs = self.vector_store.similarity_search(query, k=k)
        if not docs:
            return "Nenhuma informação encontrada na base de conhecimento."
        return "\n\n".join([doc.page_content for doc in docs])

    def search_bm25(self, query: str, k: int = 3) -> list[Document]:
        """BM25 keyword search."""
        if not self.bm25_retriever:
            return []
        return self.bm25_retriever.invoke(query, k=k)

    def search_hybrid(self, query: str, k: int = 3) -> list[Document]:
        """Hybrid: vector + BM25 via custom HybridRetriever."""
        if not self.hybrid_retriever:
            logger.warning(
                "BM25 retriever not available, falling back to vector search only."
            )
            return self.vector_store.similarity_search(query, k=k)
        # Update k dynamically if needed, or use default from initialization
        self.hybrid_retriever.k = k
        return self.hybrid_retriever.invoke(query)

    async def add_documents(self, documents: list[Document]):
        """Adiciona docs, persiste e atualiza retrievers. Thread-safe via asyncio.Lock."""
        # B-027: lock previne race condition em _all_documents e no índice BM25
        async with self._lock:
            self._all_documents.extend(documents)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.vector_store.add_documents, documents)
            self._rebuild_bm25()

    async def ingest_file(self, file_path: str):
        """Ingestão de arquivo."""
        documents = self.file_service.process_file(file_path)
        await self.add_documents(documents)

    async def ingest_url(self, url: str):
        """Ingestão de URL."""
        documents = self.web_service.process_url(url)
        await self.add_documents(documents)

    def list_documents(self) -> list[dict]:
        """
        Lista todos os documentos únicos (fontes) armazenados no ChromaDB.
        Retorna uma lista de metadados únicos baseados na chave 'source'.
        """
        try:
            # Obtemos metadados da coleção
            res = self.vector_store.get(include=["metadatas"])
            metadatas = res.get("metadatas", [])

            # Extraímos fontes únicas
            unique_sources = {}
            for meta in metadatas:
                source = meta.get("source", "unknown")
                if source not in unique_sources:
                    unique_sources[source] = {
                        "doc_id": source,  # Usamos o source como ID lógico único
                        "name": Path(source).name
                        if not source.startswith("http")
                        else source,
                        "source": source,
                        "type": "url" if source.startswith("http") else "file",
                    }

            return list(unique_sources.values())
        except Exception:
            return []

    def delete_document(self, doc_id: str):
        """
        Remove todos os chunks associados a um doc_id (source).
        """
        # No Chroma via LangChain, podemos deletar usando filtros de metadados
        self.vector_store.delete(where={"source": doc_id})

        self._all_documents = [
            d for d in self._all_documents if d.metadata.get("source") != doc_id
        ]
        # B-028: reconstrói BM25 imediatamente para não retornar chunks deletados
        self._rebuild_bm25()
