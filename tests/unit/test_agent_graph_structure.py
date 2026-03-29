from langchain_core.messages import HumanMessage

from app.processing.agent import AgentOrchestrator


async def test_graph_structure():
    orchestrator = AgentOrchestrator()
    await orchestrator._ensure_initialized()
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


def test_event_loop_continua_sem_iteracoes():
    orchestrator = AgentOrchestrator()
    state = {"messages": [HumanMessage(content="test")], "iteration_count": 0}
    assert orchestrator.event_loop(state) == "execute_tools"


def test_event_loop_termina_ao_atingir_max_iterations():
    orchestrator = AgentOrchestrator()
    # MAX_ITERATIONS padrão é 2
    state = {"messages": [HumanMessage(content="test")], "iteration_count": 2}
    assert orchestrator.event_loop(state) == "extract_knowledge"


def test_event_loop_sem_iteration_count_no_estado():
    """Estado sem iteration_count deve continuar (valor padrão 0)."""
    orchestrator = AgentOrchestrator()
    state = {"messages": [HumanMessage(content="test")]}
    assert orchestrator.event_loop(state) == "execute_tools"
