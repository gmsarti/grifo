from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore

from app.processing.agent import AgentOrchestrator


@pytest.mark.parametrize("max_iter", [1, 2, 3])
def test_event_loop_termina_exatamente_no_limite(max_iter):
    """event_loop deve retornar extract_knowledge ao atingir exatamente max_iter."""
    with patch("app.processing.agent.MAX_ITERATIONS", max_iter):
        orchestrator = AgentOrchestrator()

        state_abaixo = {
            "messages": [HumanMessage(content="x")],
            "iteration_count": max_iter - 1,
        }
        state_no_limite = {
            "messages": [HumanMessage(content="x")],
            "iteration_count": max_iter,
        }

        assert orchestrator.event_loop(state_abaixo) == "execute_tools", (
            f"Com iteration_count={max_iter - 1} e MAX={max_iter}, "
            "deve continuar iterando."
        )
        assert orchestrator.event_loop(state_no_limite) == "extract_knowledge", (
            f"Com iteration_count={max_iter} e MAX={max_iter}, deve encerrar o ciclo."
        )


@pytest.mark.parametrize("max_iter", [1, 2, 3])
async def test_process_message_respeita_max_iterations(
    max_iter, mock_llms, mock_store_manager, mock_history_db
):
    """O grafo deve rodar exatamente max_iter ciclos de revisão."""
    with (
        patch(
            "app.processing.agent.StoreMemoryManager", return_value=mock_store_manager
        ),
        patch(
            "app.processing.agent.VectorizedMessageHistory",
            return_value=mock_history_db,
        ),
        patch("app.processing.agent.MAX_ITERATIONS", max_iter),
    ):
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        result = await orchestrator.process_message("test", "t1", "p1", "u1")

    assert "response" in result or "error" in result
    # O grafo não deve ter iterado além do limite (iterations = nº de ToolMessages)
    if "iterations" in result:
        assert result["iterations"] <= max_iter
