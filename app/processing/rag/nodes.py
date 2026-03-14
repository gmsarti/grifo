from typing import Any, Dict
from langchain_core.documents import Document
from app.data_source.vector_store import VectorStoreManager
from app.processing.rag.state import GraphState
from app.processing.rag.chains import (
    get_retrieval_grader,
    get_rag_generation_chain,
    get_question_rewriter,
)
from app.core.logging import get_logger, timed_process
from langchain_community.tools.tavily_search import TavilySearchResults

logger = get_logger(__name__)

def retrieve(state: GraphState) -> Dict[str, Any]:
    """
    Retrieve documents from vectorstore
    """
    question = state["question"]
    project_id = state.get("project_id", "default")
    metadata = {"question": question, "project_id": project_id}
    
    with timed_process("RAG Retrieve", logger, metadata=metadata):
        # Retrieval (Project-scoped)
        manager = VectorStoreManager(project_id=project_id)
        documents = manager.search(query=question, search_type="hybrid", k=3)
    
    return {"documents": documents, "question": question}

def generate(state: GraphState) -> Dict[str, Any]:
    """
    Generate answer
    """
    question = state["question"]
    documents = state["documents"]
    metadata = {"question": question, "documents_count": len(documents)}
    
    with timed_process("RAG Generate", logger, metadata=metadata):
        # RAG generation
        rag_chain = get_rag_generation_chain()
        generation = rag_chain.invoke({"context": documents, "question": question})
    
    return {"generation": generation.content, "question": question}

def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question.
    """
    question = state["question"]
    documents = state["documents"]
    metadata = {"question": question, "documents_count": len(documents)}
    
    with timed_process("RAG Grade Documents", logger, metadata=metadata):
        # Score each doc
        grader = get_retrieval_grader()
        filtered_docs = []
        web_search = False
        
        for d in documents:
            score = grader.invoke({"question": question, "document": d.page_content})
            grade = score.binary_score
            
            if grade == "yes":
                logger.info("---GRADE: DOCUMENT RELEVANT---", extra={"metadata": {"doc_source": d.metadata.get("source")}})
                filtered_docs.append(d)
            else:
                logger.info("---GRADE: DOCUMENT NOT RELEVANT---", extra={"metadata": {"doc_source": d.metadata.get("source")}})
                web_search = True
                continue
                
        # If no relevant documents found, we signal web search
        if not filtered_docs:
            web_search = True
        
    return {"documents": filtered_docs, "question": question, "web_search": web_search}

def web_search(state: GraphState) -> Dict[str, Any]:
    """
    Web search based based on the re-phrased question.
    """
    question = state["question"]
    documents = state.get("documents", [])
    metadata = {"question": question}
    
    with timed_process("RAG Web Search", logger, metadata=metadata):
        # Re-write question
        rewriter = get_question_rewriter()
        better_question = rewriter.invoke({"question": question})
        
        # Web search
        from app.core.config import settings
        search = TavilySearchResults(k=3, tavily_api_key=settings.TAVILY_API_KEY)
        results = search.invoke({"query": better_question.content})
        
        web_results = "\n".join([d["content"] for d in results])
        web_results = Document(page_content=web_results, metadata={"source": "web_search"})
        
        documents.append(web_results)
    
    return {"documents": documents, "question": question}
