import pytest
from app.processing.rag.chains import get_retrieval_grader, get_rag_generation_chain, get_question_rewriter
from langchain_core.documents import Document

def test_retrieval_grader():
    """Test the retrieval grader chain."""
    grader = get_retrieval_grader()
    
    # Test relevant document
    res_yes = grader.invoke({
        "question": "O que é o Grifo?",
        "document": "Grifo é um framework de agentes inteligentes."
    })
    assert res_yes.binary_score in ["yes", "no"] # LLM output validation
    
    # Test irrelevant document
    res_no = grader.invoke({
        "question": "Qual a cor do céu?",
        "document": "O preço da maçã subiu ontem."
    })
    assert res_no.binary_score in ["yes", "no"]

def test_rag_generation_chain():
    """Test the RAG generation chain."""
    chain = get_rag_generation_chain()
    
    context = "Grifo é um sistema de automação. Ele usa LangGraph."
    question = "O que é o Grifo?"
    
    res = chain.invoke({"context": context, "question": question})
    assert res.content is not None
    assert len(res.content) > 0

def test_question_rewriter():
    """Test the question rewriter chain."""
    rewriter = get_question_rewriter()
    
    question = "Como funciona o RAG no Grifo?"
    res = rewriter.invoke({"question": question})
    
    assert res.content is not None
    assert len(res.content) > 0
