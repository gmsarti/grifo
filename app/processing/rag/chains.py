from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm import get_fast_model, get_reasoner

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

def get_retrieval_grader():
    """Returns the retrieval grader chain."""
    llm = get_fast_model()
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
    
    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
        ]
    )

    return grade_prompt | structured_llm_grader

def get_rag_generation_chain():
    """Returns the RAG generation chain."""
    llm = get_reasoner() # Using reasoner for better synthesis

    template = """You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Use three sentences maximum and keep the answer concise.
    
    Question: {question} 
    Context: {context} 
    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    return prompt | llm

def get_question_rewriter():
    """Returns the question rewriter chain."""
    llm = get_fast_model()

    system = """You are a question re-writer that converts an input question to a better version that is optimized \n 
     for web search. Look at the input and try to reason about the underlying semantic intent / meaning."""
    
    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Here is the initial question: \n\n {question} \n Formulate an improved version.",
            ),
        ]
    )

    return re_write_prompt | llm
