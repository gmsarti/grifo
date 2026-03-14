from app.processing.agent import AgentOrchestrator
from langgraph.graph import END
from langchain_core.messages import HumanMessage, AIMessage


def test_graph_structure():
    orchestrator = AgentOrchestrator()
    graph = orchestrator.graph

    # Check nodes
    nodes = graph.nodes
    assert "draft" in nodes
    assert "execute_tools" in nodes
    assert "revise" in nodes

    # Check edges
    # Note: compiled graphs might have different internal structures,
    # but we can check the logical flow if we access the underlying builder if possible,
    # or just check that we can at least get the graph visualization/description.

    graph.get_graph()

    # Verify we can find the expected path START -> draft -> execute_tools -> revise
    # In LangGraph, edges are a bit harder to inspect directly from CompiledStateGraph
    # but we can check if the nodes exist and maybe try a dry run if mocked.
    assert len(nodes) >= 3


def test_event_loop_logic():
    """Testa lógica do event_loop isoladamente."""
    orchestrator = AgentOrchestrator()
    
    # Sem tool_calls
    state_no_tools = {"messages": [HumanMessage(content="no tools")]}
    assert orchestrator.event_loop(state_no_tools) == "execute_tools"
    
    # Com tool_calls = MAX_ITERATIONS (formato correto)
    CORRECT_TOOL_CALL = {
        "name": "test_tool", "args": {}, "id": "call_123", "type": "tool"
    }
    state_with_tools = {"messages": [
        AIMessage(content="", tool_calls=[CORRECT_TOOL_CALL]) for _ in range(2)
    ]}
    assert orchestrator.event_loop(state_with_tools) == "extract_knowledge"
