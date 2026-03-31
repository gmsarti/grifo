from langchain_core.messages import HumanMessage

from app.processing.agent import AgentOrchestrator


async def test_graph_has_reflexion_nodes():
    orchestrator = AgentOrchestrator()
    await orchestrator._ensure_initialized()
    nodes = orchestrator.graph.nodes
    assert "draft" in nodes
    assert "execute_tools" in nodes
    assert "revise" in nodes


async def test_graph_has_router_node():
    orchestrator = AgentOrchestrator()
    await orchestrator._ensure_initialized()
    assert "classify" in orchestrator.graph.nodes


async def test_graph_has_arq_extract_node():
    orchestrator = AgentOrchestrator()
    await orchestrator._ensure_initialized()
    assert "arq_extract" in orchestrator.graph.nodes


async def test_graph_is_renderable():
    """Garante que o grafo compilado pode ser inspecionado sem erros."""
    orchestrator = AgentOrchestrator()
    await orchestrator._ensure_initialized()
    orchestrator.graph.get_graph()  # não deve lançar exceção


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
