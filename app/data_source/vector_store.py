from typing import List
from langchain_chroma import Chroma  # Oficial para LangChain/Chroma integration
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from app.core.config import settings
from app.data_source.loaders import FileIngestionService, WebIngestionService


from pydantic import ConfigDict

class HybridRetriever(BaseRetriever):
    """
    Custom Retriever that combines Vector Search and BM25 using
    Reciprocal Rank Fusion (RRF).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vector_retriever: BaseRetriever
    bm25_retriever: BaseRetriever
    k: int = 4

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
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

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings,
        )
        self.file_service = FileIngestionService()
        self.web_service = WebIngestionService()
        self.bm25_retriever = None
        self.hybrid_retriever = None  # replaced ensemble
        self._all_documents = []  # Track all docs for BM25 updates

    def search_context(self, query: str, k: int = 3) -> str:
        """Busca semântica pura via vector store."""
        docs = self.vector_store.similarity_search(query, k=k)
        if not docs:
            return "Nenhuma informação encontrada na base de conhecimento."
        return "\n\n".join([doc.page_content for doc in docs])

    def search_bm25(self, query: str, k: int = 3) -> List[Document]:
        """BM25 keyword search."""
        if not self.bm25_retriever:
            return []
        return self.bm25_retriever.invoke(query, k=k)

    def search_hybrid(self, query: str, k: int = 3) -> List[Document]:
        """Hybrid: vector + BM25 via custom HybridRetriever."""
        if not self.hybrid_retriever:
            return self.vector_store.similarity_search(query, k=k)
        # Update k dynamically if needed, or use default from initialization
        self.hybrid_retriever.k = k
        return self.hybrid_retriever.invoke(query)

    def add_documents(self, documents: List[Document]):
        """Adiciona docs, persiste e atualiza retrievers."""
        self._all_documents.extend(documents)
        self.vector_store.add_documents(documents)
        self.vector_store.persist()

        if self._all_documents:
            self.bm25_retriever = BM25Retriever.from_documents(
                self._all_documents,
                k=5,
            )
            # Custom Hybrid Retriever with RRF
            self.hybrid_retriever = HybridRetriever(
                vector_retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
                bm25_retriever=self.bm25_retriever,
                k=5,
            )

    def ingest_file(self, file_path: str):
        """Ingestão de arquivo."""
        documents = self.file_service.process_file(file_path)
        self.add_documents(documents)

    def ingest_url(self, url: str):
        """Ingestão de URL."""
        documents = self.web_service.process_url(url)
        self.add_documents(documents)
