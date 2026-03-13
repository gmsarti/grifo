from app.processing.agent import AgentOrchestrator
from langgraph.graph import END


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
    orchestrator = AgentOrchestrator()
    from langchain_core.messages import ToolMessage, AIMessage

    # Mock state with 0 tool visits
    state = {"messages": [AIMessage(content="[FAST] test")]}
    assert orchestrator.event_loop(state) == "execute_tools"

    # Mock state with MAX_ITERATIONS (2) tool visits
    state = {
        "messages": [
            ToolMessage(content="r1", tool_call_id="1"),
            ToolMessage(content="r2", tool_call_id="2"),
        ]
    }
    # Since MAX_ITERATIONS = 2, it should return END when count >= 2
    assert orchestrator.event_loop(state) == END
