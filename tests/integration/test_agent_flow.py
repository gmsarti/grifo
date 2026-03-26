from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.store.memory import InMemoryStore

from app.processing.agent import AgentOrchestrator
from app.processing.memory import StoreMemoryManager
from app.schemas.agent_schemas import ExtractedFact, KnowledgeExtraction


@pytest.mark.asyncio
async def test_agent_orchestrator_initialization():
    # Use real objects here to pass ensure_valid_checkpointer
    orchestrator = AgentOrchestrator()
    assert orchestrator.graph is not None
    assert orchestrator.first_responder is not None
    assert orchestrator.revisor is not None


@pytest.mark.asyncio
async def test_agent_process_message_mocked():
    with patch("app.processing.agent.VectorizedMessageHistory") as mock_hist_class:
        # Correctly mock the instance methods
        mock_hist_instance = mock_hist_class.return_value
        mock_hist_instance.add_message = AsyncMock()

        orchestrator = AgentOrchestrator()

        # Mock the graph execution
        with patch.object(
            orchestrator.graph, "ainvoke", new_callable=AsyncMock
        ) as mock_invoke:
            from langchain_core.messages import AIMessage

            mock_invoke.return_value = {
                "messages": [AIMessage(content="Final response content")]
            }

            response = await orchestrator.process_message(
                "What is the company policy?",
                thread_id="test_thread",
                project_id="test_project",
            )

            assert response["response"] == "Final response content"
            mock_invoke.assert_called_once()
            _, kwargs = mock_invoke.call_args
            # thread_id no configurable é o invocation_id (UUID por chamada para isolamento
            # do checkpointer); o thread real do usuário fica em user_thread_id
            assert kwargs["config"]["configurable"]["user_thread_id"] == "test_thread"
            mock_hist_instance.add_message.assert_called()


@pytest.mark.asyncio
async def test_knowledge_saved_to_real_store_after_extraction():
    """
    Integração: extract_knowledge_node deve salvar fatos no InMemoryStore real.
    Verifica que save_fact efetivamente persiste dados recuperáveis via search_memories.
    """
    store = InMemoryStore()
    manager = StoreMemoryManager(store)

    await manager.save_fact(
        "user_integ",
        "fact_001",
        "[Interesse de Pesquisa] Usuário pesquisa LLMs",
        thread_id="t1",
    )
    await manager.save_fact(
        "user_integ", "fact_002", "[Tecnologia] Usuário usa LangChain", thread_id="t1"
    )

    results = await manager.search_memories("user_integ", "LLM language model")

    assert len(results) > 0, (
        "Fatos não foram encontrados após salvar. "
        "Verifique se save_fact usa tuple para namespace."
    )
    all_contents = " ".join(r.value["content"] for r in results)
    assert "LLMs" in all_contents or "LangChain" in all_contents


@pytest.mark.asyncio
async def test_knowledge_retrieved_on_next_message():
    """
    Integração completa: fatos extraídos na primeira mensagem devem ser
    recuperados e injetados no contexto da segunda mensagem.

    Fluxo:
      1. extract_knowledge_node salva fato no store
      2. retrieve_memory_node da próxima mensagem encontra o fato
      3. Fato aparece no SystemMessage de contexto
    """
    TOOL_CALL = {
        "name": "revise_answer_tool",
        "args": {
            "answer": "Django é um framework web Python de alto nível.",
            "reflection": {},
            "search_queries": [],
            "references": [],
        },
        "id": "call_001",
        "type": "tool",
    }

    mock_extract = MagicMock()
    mock_extract.ainvoke = AsyncMock(
        return_value=KnowledgeExtraction(
            facts=[
                ExtractedFact(fact="Usuário trabalha com Django", topic="Tecnologia")
            ]
        )
    )

    mock_history_db = MagicMock()
    mock_history_db.search_history.return_value = ""
    mock_history_db.add_message = AsyncMock()

    with (
        patch("app.processing.agent.get_first_responder"),
        patch("app.processing.agent.get_revisor"),
        patch(
            "app.processing.agent.get_knowledge_extractor", return_value=mock_extract
        ),
        patch(
            "app.processing.agent.VectorizedMessageHistory",
            return_value=mock_history_db,
        ),
    ):
        store = InMemoryStore()
        orchestrator = AgentOrchestrator(store=store)

        # Passo 1: extrai e salva o fato via extract_knowledge_node
        state = {
            "messages": [
                HumanMessage(content="Como uso Django com PostgreSQL?"),
                AIMessage(content="", tool_calls=[TOOL_CALL]),
            ]
        }
        config = {
            "configurable": {
                "user_id": "user_flow",
                "user_thread_id": "thread_flow",
                "thread_id": "invocation_uuid",
            }
        }
        await orchestrator.extract_knowledge_node(state, config)

        # Passo 2: segunda mensagem — retrieve_memory_node deve encontrar o fato
        state2 = {"messages": [HumanMessage(content="Qual ORM devo usar?")]}
        config2 = {
            "configurable": {
                "thread_id": "t2",
                "user_id": "user_flow",
                "project_id": "proj1",
            }
        }
        result = await orchestrator.retrieve_memory_node(state2, config2)

        injected_messages = result.get("messages", [])
        has_fact = any(
            isinstance(m, SystemMessage) and "Django" in m.content
            for m in injected_messages
        )
        assert has_fact, (
            "Fato salvo na primeira interação não foi recuperado na segunda. "
            "Verifique namespaces em save_fact e search_memories."
        )


@pytest.mark.asyncio
async def test_researcher_profile_propagates_to_draft():
    """
    Integração: fatos sobre o pesquisador salvos no store devem aparecer
    no contexto do draft_node na próxima mensagem.

    Fluxo:
      1. Salva fatos do pesquisador no store
      2. retrieve_memory_node os injeta como SystemMessage
      3. draft_node recebe o SystemMessage com o perfil
    """
    TOOL_CALL = {
        "name": "answer_question_tool",
        "args": {"answer": "resposta mock", "reflection": {}, "search_queries": []},
        "id": "c1",
        "type": "tool",
    }

    captured_draft_input = {}

    async def capturing_first_responder(inputs):
        captured_draft_input["messages"] = inputs["messages"]
        return AIMessage(content="", tool_calls=[TOOL_CALL])

    mock_draft = MagicMock()
    mock_draft.ainvoke = capturing_first_responder

    mock_revise = MagicMock()
    mock_revise.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="",
            tool_calls=[
                {
                    **TOOL_CALL,
                    "name": "revise_answer_tool",
                    "args": {**TOOL_CALL["args"], "references": []},
                }
            ],
        )
    )
    mock_extract = MagicMock()
    mock_extract.ainvoke = AsyncMock(return_value=KnowledgeExtraction(facts=[]))

    mock_history_db = MagicMock()
    mock_history_db.search_history.return_value = ""
    mock_history_db.add_message = AsyncMock()

    with (
        patch("app.processing.agent.get_first_responder", return_value=mock_draft),
        patch("app.processing.agent.get_revisor", return_value=mock_revise),
        patch(
            "app.processing.agent.get_knowledge_extractor", return_value=mock_extract
        ),
        patch(
            "app.processing.agent.VectorizedMessageHistory",
            return_value=mock_history_db,
        ),
    ):
        store = InMemoryStore()
        orchestrator = AgentOrchestrator(store=store)

        # Salva perfil do pesquisador diretamente no store
        from app.processing.memory import StoreMemoryManager

        manager = StoreMemoryManager(store)
        await manager.save_fact(
            "researcher_bio",
            "fact_001",
            "[Contexto de Trabalho] Pesquisadora de doutorado em biologia sintética",
        )
        await manager.save_fact(
            "researcher_bio",
            "fact_002",
            "[Nível Técnico] Especialista em engenharia metabólica e CRISPR",
        )

        # Processa mensagem — retrieve_memory_node deve injetar o perfil
        await orchestrator.process_message(
            "Quais são os limites atuais de edição gênica multiplex?",
            thread_id="t_bio",
            project_id="biosynth",
            user_id="researcher_bio",
        )

        messages_to_draft = captured_draft_input.get("messages", [])
        profile_injected = any(
            isinstance(m, SystemMessage)
            and ("biologia sintética" in m.content or "CRISPR" in m.content)
            for m in messages_to_draft
        )
        assert profile_injected, (
            "O perfil do pesquisador salvo no store não chegou ao draft_node. "
            "Verifique retrieve_memory_node e o fluxo de mensagens no grafo."
        )


@pytest.mark.asyncio
async def test_tool_executor_crag_flow():
    # This test verifies the logic in tool_executor's run_queries
    from app.processing.tool_executor import run_queries

    with (
        patch("app.processing.tool_executor.VectorStoreManager") as mock_vdb_class,
        patch("app.processing.tool_executor.get_tavily_tool") as mock_get_tavily,
        patch("app.processing.tool_executor.get_grader_llm") as mock_get_grader,
    ):
        # Setup mock instances
        mock_vdb = mock_vdb_class.return_value
        mock_tavily = mock_get_tavily.return_value
        mock_grader = mock_get_grader.return_value

        # Scenario: Local search returns irrelevant docs -> Fallback to Tavily
        mock_vdb.search_hybrid.return_value = [
            MagicMock(page_content="Some irrelevant local doc")
        ]
        mock_grader.ainvoke = AsyncMock(return_value=MagicMock(content="NO"))
        mock_tavily.ainvoke = AsyncMock(return_value="Web result content")

        result = await run_queries(["test query"])

        assert "Web result content" in result
        mock_vdb.search_hybrid.assert_called_with("test query", k=3)
        mock_tavily.ainvoke.assert_called_once()
