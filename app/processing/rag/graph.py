from langgraph.graph import END, StateGraph, START
from app.processing.rag.state import GraphState
from app.processing.rag.nodes import retrieve, grade_documents, generate, web_search

def decide_to_generate(state: GraphState):
    """
    Determines whether to generate an answer, or re-generate a question.
    
    Args:
        state (dict): The current graph state
        
    Returns:
        str: Binary decision for next node to call
    """
    web_search_flag = state["web_search"]
    
    if web_search_flag:
        return "web_search"
    else:
        return "generate"

def create_rag_graph():
    """
    Creates the Agentic RAG graph.
    """
    workflow = StateGraph(GraphState)
    
    # Define the nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("web_search", web_search)
    
    # Build graph
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "web_search": "web_search",
            "generate": "generate",
        },
    )
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()
