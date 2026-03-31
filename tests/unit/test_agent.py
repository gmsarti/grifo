from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from langgraph.store.memory import InMemoryStore

from app.core.config import settings
from app.processing.agent import AgentOrchestrator
from app.processing.router_chain import RouterDecision
from app.schemas.agent_schemas import ExtractedFact, KnowledgeExtraction
from app.schemas.arq_schemas import ExtrairPadroesResponse


@pytest.fixture
def mock_settings():
    with patch("app.core.config.settings.REFLEXION_MAX_ITERATIONS", 1):
        yield


class TestAgentOrchestrator:
    """Testes completos."""

    async def test_initialization(self, mock_llms, mock_store_manager):
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        await orchestrator._ensure_initialized()
        assert orchestrator.graph is not None
        assert isinstance(orchestrator.reflexion_tools, ToolNode)

    async def test_single_iteration(
        self, mock_llms, mock_store_manager, mock_history_db, mock_settings
    ):
        # Patch class constructors: intercepts instantiation inside AgentOrchestrator
        with (
            patch(
                "app.processing.agent.StoreMemoryManager",
                return_value=mock_store_manager,
            ),
            patch(
                "app.processing.agent.VectorizedMessageHistory",
                return_value=mock_history_db,
            ),
        ):
            orchestrator = AgentOrchestrator(store=InMemoryStore())

            result = await orchestrator.process_message(
                "Test", "thread1", "proj1", "user1"
            )

            assert "response" in result
            assert "usage" in result
            assert result["response"] is not None

    async def test_event_loop_terminates(
        self, mock_llms, mock_store_manager, mock_history_db
    ):
        settings.REFLEXION_MAX_ITERATIONS = 1
        with (
            patch(
                "app.processing.agent.StoreMemoryManager",
                return_value=mock_store_manager,
            ),
            patch(
                "app.processing.agent.VectorizedMessageHistory",
                return_value=mock_history_db,
            ),
        ):
            orchestrator = AgentOrchestrator(store=InMemoryStore())

            result = await orchestrator.process_message("test", "t1", "p1")
            assert "iterations" in result
            assert result["iterations"] <= 2  # Draft + Revise

    async def test_memory_retrieval(
        self, mock_llms, mock_store_manager, mock_history_db
    ):
        # mock_history_db já é MagicMock com search_history dummy
        mock_history_db.search_history.return_value = "Mock history"

        with (
            patch(
                "app.processing.agent.StoreMemoryManager",
                return_value=mock_store_manager,
            ),
            patch(
                "app.processing.agent.VectorizedMessageHistory",
                return_value=mock_history_db,
            ),
        ):
            orchestrator = AgentOrchestrator(store=InMemoryStore())

            state = {"messages": [HumanMessage(content="test")]}
            config = {
                "configurable": {"thread_id": "t1", "user_id": "u1", "project_id": "p1"}
            }

            result = await orchestrator.retrieve_memory_node(state, config)

            assert len(result["messages"]) == 1
            assert "Relevant Conversation History" in result["messages"][0].content

    async def test_knowledge_extraction_empty(self, mock_llms, mock_store_manager):
        # Mock extractor retorna lista vazia
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(facts=[])

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {"messages": [AIMessage(content="test")]}
        config = {"configurable": {"user_id": "test-user"}}

        await orchestrator.extract_knowledge_node(state, config)

        mock_store_manager.save_fact.assert_not_called()

    async def test_knowledge_extraction_success(self, mock_llms, mock_store_manager):
        # Mock extractor retorna um fato
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(
            facts=[ExtractedFact(fact="User likes Python", topic="preferences")]
        )

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {
            "messages": [
                HumanMessage(content="Eu gosto de Python"),
                AIMessage(content="Que legal!"),
            ]
        }
        config = {"configurable": {"user_id": "test-user"}}

        await orchestrator.extract_knowledge_node(state, config)

        mock_store_manager.save_fact.assert_called_once()
        args, kwargs = mock_store_manager.save_fact.call_args
        assert args[0] == "test-user"
        assert "User likes Python" in args[2]


class TestExtractKnowledgeNode:
    """Testes focados no comportamento do nó de extração de conhecimento."""

    async def test_uses_user_thread_id_not_invocation_id(
        self, mock_llms, mock_store_manager
    ):
        """
        process_message salva o thread real em 'user_thread_id' e um UUID por invocação
        em 'thread_id'. extract_knowledge_node deve usar 'user_thread_id'.
        """
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(
            facts=[ExtractedFact(fact="some fact", topic="Test")]
        )

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {"messages": [HumanMessage(content="test")]}
        config = {
            "configurable": {
                "user_id": "user1",
                "thread_id": "invocation_uuid_should_be_ignored",
                "user_thread_id": "real_thread_abc",
            }
        }

        await orchestrator.extract_knowledge_node(state, config)

        _, kwargs = mock_store_manager.save_fact.call_args
        assert kwargs.get("thread_id") == "real_thread_abc", (
            "save_fact deve receber o thread real ('user_thread_id'), "
            "não o UUID de invocação ('thread_id')."
        )

    async def test_research_conversation_extracts_topic_of_interest(
        self, mock_llms, mock_store_manager
    ):
        """
        Uma conversa de pesquisa (Q&A técnico) deve gerar fatos sobre
        tópicos de interesse, não apenas preferências pessoais.
        """
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(
            facts=[
                ExtractedFact(
                    fact="Usuário está pesquisando computação quântica",
                    topic="Interesse de Pesquisa",
                )
            ]
        )

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {
            "messages": [
                HumanMessage(content="O que são qubits e como funcionam?"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "revise_answer_tool",
                            "args": {
                                "answer": "Qubits são a unidade básica da computação quântica...",
                                "reflection": {},
                                "search_queries": [],
                                "references": [],
                            },
                            "id": "call_001",
                            "type": "tool",
                        }
                    ],
                ),
            ]
        }
        config = {"configurable": {"user_id": "researcher1", "user_thread_id": "t1"}}

        await orchestrator.extract_knowledge_node(state, config)

        mock_store_manager.save_fact.assert_called_once()
        args, _ = mock_store_manager.save_fact.call_args
        formatted_fact = args[2]
        assert (
            "Interesse de Pesquisa" in formatted_fact
            or "pesquisando" in formatted_fact.lower()
        )

    async def test_history_builder_captures_tool_call_answers(
        self, mock_llms, mock_store_manager
    ):
        """
        Quando a IA usa tool_calls (padrão Reflexion), a resposta fica em
        tool_calls[].args['answer'] — o history builder deve extrair esse conteúdo.
        O knowledge extractor deve receber a resposta da IA, não uma string vazia.
        """
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(facts=[])

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        ai_answer = "Python é uma linguagem de alto nível muito usada em data science."
        state = {
            "messages": [
                HumanMessage(content="O que é Python?"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "revise_answer_tool",
                            "args": {
                                "answer": ai_answer,
                                "reflection": {},
                                "search_queries": [],
                                "references": [],
                            },
                            "id": "call_001",
                            "type": "tool",
                        }
                    ],
                ),
            ]
        }
        config = {"configurable": {"user_id": "user1", "user_thread_id": "t1"}}

        await orchestrator.extract_knowledge_node(state, config)

        # Verifica que o extractor recebeu um history com a resposta da IA
        call_args = mock_extract.ainvoke.call_args
        history = (
            call_args.args[0]["history"]
            if call_args.args
            else call_args.kwargs["history"]
        )
        assert "Python é uma linguagem" in history, (
            "A resposta da IA em tool_calls.args['answer'] não foi incluída no history. "
            "O extractor recebeu contexto insuficiente para extrair fatos."
        )

    async def test_history_builder_ignores_tool_messages(
        self, mock_llms, mock_store_manager
    ):
        """
        ToolMessages (execução das tools) não devem aparecer no history
        enviado ao knowledge extractor — eles contêm dados estruturados, não texto.
        """
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(facts=[])

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {
            "messages": [
                HumanMessage(content="Pergunta do usuário"),
                ToolMessage(content='{"documents": []}', tool_call_id="call_001"),
                AIMessage(content="Resposta da IA"),
            ]
        }
        config = {"configurable": {"user_id": "user1", "user_thread_id": "t1"}}

        await orchestrator.extract_knowledge_node(state, config)

        call_args = mock_extract.ainvoke.call_args
        history = (
            call_args.args[0]["history"]
            if call_args.args
            else call_args.kwargs["history"]
        )
        assert '{"documents"' not in history

    async def test_extraction_error_does_not_raise(self, mock_llms, mock_store_manager):
        """Erro durante extração não deve propagar — o nó degrada graciosamente."""
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.side_effect = Exception("LLM unavailable")

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {"messages": [HumanMessage(content="test")]}
        config = {"configurable": {"user_id": "user1", "user_thread_id": "t1"}}

        # Não deve lançar exceção
        result = await orchestrator.extract_knowledge_node(state, config)
        assert result == {"messages": []}

    async def test_empty_message_list_skips_extraction(
        self, mock_llms, mock_store_manager
    ):
        """Com estado sem mensagens relevantes, extração não deve ser invocada."""
        mock_draft, mock_revise, mock_extract = mock_llms

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        # Apenas ToolMessages — sem HumanMessage nem AIMessage com conteúdo
        state = {
            "messages": [
                ToolMessage(content='{"result": "ok"}', tool_call_id="c1"),
            ]
        }
        config = {"configurable": {"user_id": "user1", "user_thread_id": "t1"}}

        await orchestrator.extract_knowledge_node(state, config)

        # extractor não deve ser chamado (history_str seria vazio)
        mock_extract.ainvoke.assert_not_called()

    async def test_multiple_facts_all_saved(self, mock_llms, mock_store_manager):
        """Quando o extractor retorna múltiplos fatos, todos devem ser salvos."""
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(
            facts=[
                ExtractedFact(fact="Usuário usa FastAPI", topic="Tecnologia"),
                ExtractedFact(
                    fact="Usuário prefere respostas curtas",
                    topic="Preferência do Usuário",
                ),
                ExtractedFact(
                    fact="Projeto usa PostgreSQL", topic="Detalhes do Projeto"
                ),
            ]
        )

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {
            "messages": [
                HumanMessage(content="Como conecto FastAPI ao PostgreSQL?"),
                AIMessage(content="Use asyncpg ou SQLAlchemy async..."),
            ]
        }
        config = {"configurable": {"user_id": "user1", "user_thread_id": "t1"}}

        await orchestrator.extract_knowledge_node(state, config)

        assert mock_store_manager.save_fact.call_count == 3

    async def test_fact_formatted_with_topic_prefix(
        self, mock_llms, mock_store_manager
    ):
        """Fato salvo deve ter o formato '[Tópico] texto do fato'."""
        mock_draft, mock_revise, mock_extract = mock_llms
        mock_extract.ainvoke.return_value = KnowledgeExtraction(
            facts=[ExtractedFact(fact="Usuário usa Django", topic="Tecnologia")]
        )

        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.store_manager = mock_store_manager

        state = {"messages": [HumanMessage(content="Falo sobre Django")]}
        config = {"configurable": {"user_id": "user1", "user_thread_id": "t1"}}

        await orchestrator.extract_knowledge_node(state, config)

        args, _ = mock_store_manager.save_fact.call_args
        formatted = args[2]
        assert formatted == "[Tecnologia] Usuário usa Django"


class TestResearcherProfileInfluence:
    """
    Testa que o perfil do pesquisador — injetado pelo retrieve_memory_node
    como SystemMessage — chega aos nós de draft e revisão e pode influenciar
    as queries e a profundidade da resposta.
    """

    async def test_researcher_profile_is_present_in_draft_node_input(
        self, mock_llms, mock_store_manager, mock_history_db
    ):
        """
        O draft_node recebe o perfil do pesquisador como SystemMessage de contexto.
        Verifica que a mensagem de memória (injetada por retrieve_memory_node) está
        presente no state quando draft_node é invocado.
        """
        mock_draft, mock_revise, mock_extract = mock_llms

        # Captura o state real passado ao first_responder
        captured_state = {}

        async def capturing_draft(inputs):
            captured_state["messages"] = inputs["messages"]
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "answer_question_tool",
                        "args": {
                            "answer": "resposta",
                            "reflection": {},
                            "search_queries": [],
                        },
                        "id": "c1",
                        "type": "tool",
                    }
                ],
            )

        mock_draft.ainvoke = capturing_draft

        researcher_context = (
            "Context from memory:\n"
            "Known Facts/Preferences:\n"
            "- [Contexto de Trabalho] Pesquisadora de doutorado em biologia molecular\n"
            "- [Nível Técnico] Especialista em CRISPR e edição gênica"
        )

        with (
            patch(
                "app.processing.agent.StoreMemoryManager",
                return_value=mock_store_manager,
            ),
            patch(
                "app.processing.agent.VectorizedMessageHistory",
                return_value=mock_history_db,
            ),
        ):
            orchestrator = AgentOrchestrator(store=InMemoryStore())

            state = {
                "messages": [
                    SystemMessage(content=researcher_context, name="memory_context"),
                    HumanMessage(content="Como CRISPR-Cas9 difere do CRISPR-Cas12?"),
                ]
            }

            await orchestrator.draft_node(state)

            messages_received = captured_state.get("messages", [])
            system_messages = [
                m for m in messages_received if isinstance(m, SystemMessage)
            ]
            has_profile = any(
                "biologia molecular" in m.content
                or "memory_context" == getattr(m, "name", "")
                for m in system_messages
            )
            assert has_profile, (
                "O draft_node não recebeu o perfil do pesquisador. "
                "O SystemMessage de memória deve estar no state antes do draft."
            )

    async def test_retrieve_memory_injects_user_facts_as_system_message(
        self, mock_llms, mock_store_manager, mock_history_db
    ):
        """
        Quando há fatos sobre o pesquisador no store, retrieve_memory_node deve
        injetá-los como SystemMessage com o perfil completo.
        """
        mock_store_manager.search_memories = AsyncMock(
            return_value=[
                MagicMock(
                    value={
                        "content": "[Contexto de Trabalho] Doutoranda em neurociência"
                    }
                ),
                MagicMock(
                    value={
                        "content": "[Interesse de Pesquisa] Conectoma e plasticidade sináptica"
                    }
                ),
            ]
        )

        with (
            patch(
                "app.processing.agent.StoreMemoryManager",
                return_value=mock_store_manager,
            ),
            patch(
                "app.processing.agent.VectorizedMessageHistory",
                return_value=mock_history_db,
            ),
        ):
            orchestrator = AgentOrchestrator(store=InMemoryStore())

            state = {"messages": [HumanMessage(content="O que é LTP?")]}
            config = {
                "configurable": {
                    "thread_id": "t1",
                    "user_id": "researcher_phd",
                    "project_id": "neurosci",
                }
            }

            result = await orchestrator.retrieve_memory_node(state, config)

            injected = result.get("messages", [])
            assert len(injected) == 1
            context_msg = injected[0]
            assert isinstance(context_msg, SystemMessage)
            assert "neurociência" in context_msg.content
            assert "plasticidade sináptica" in context_msg.content

    async def test_retrieve_memory_combines_history_and_user_facts(
        self, mock_llms, mock_store_manager, mock_history_db
    ):
        """
        O contexto injetado deve combinar histórico vetorizado E fatos de longo prazo
        para dar ao pesquisador uma visão completa do contexto.
        """
        mock_history_db.search_history.return_value = (
            "User: Preciso de artigos sobre BDNF\n"
            "Assistant: BDNF é um fator neurotrófico..."
        )
        mock_store_manager.search_memories = AsyncMock(
            return_value=[
                MagicMock(
                    value={
                        "content": "[Nível Técnico] Especialista em neurobiologia molecular"
                    }
                ),
            ]
        )

        with (
            patch(
                "app.processing.agent.StoreMemoryManager",
                return_value=mock_store_manager,
            ),
            patch(
                "app.processing.agent.VectorizedMessageHistory",
                return_value=mock_history_db,
            ),
        ):
            orchestrator = AgentOrchestrator(store=InMemoryStore())

            state = {"messages": [HumanMessage(content="BDNF e depressão")]}
            config = {
                "configurable": {
                    "thread_id": "t1",
                    "user_id": "u1",
                    "project_id": "p1",
                }
            }

            result = await orchestrator.retrieve_memory_node(state, config)
            context_content = result["messages"][0].content

            assert "Relevant Conversation History" in context_content
            assert "Known Facts/Preferences" in context_content
            assert "neurobiologia" in context_content
            assert "BDNF" in context_content


# ── TestRouteAfterClassify ────────────────────────────────────────────────────


class TestRouteAfterClassify:
    """Testa a função de roteamento pura — sem I/O, sem LLM."""

    def test_returns_arq_extract_when_arq_intent_and_zona_present(self):
        orchestrator = AgentOrchestrator()
        state = {
            "messages": [],
            "intent": "arq_extract",
            "zona": "quarto",
            "mobiliario": ["cama"],
        }
        assert orchestrator.route_after_classify(state) == "arq_extract"

    def test_falls_back_to_reflexion_when_arq_intent_but_no_zona(self):
        """Sem zona identificada não é possível extrair padrões."""
        orchestrator = AgentOrchestrator()
        state = {
            "messages": [],
            "intent": "arq_extract",
            "zona": None,
            "mobiliario": [],
        }
        assert orchestrator.route_after_classify(state) == "retrieve_memory"

    def test_falls_back_to_reflexion_when_reflexion_intent(self):
        orchestrator = AgentOrchestrator()
        state = {
            "messages": [],
            "intent": "reflexion",
            "zona": "quarto",
            "mobiliario": [],
        }
        assert orchestrator.route_after_classify(state) == "retrieve_memory"

    def test_falls_back_to_reflexion_when_intent_absent_from_state(self):
        orchestrator = AgentOrchestrator()
        state = {"messages": []}
        assert orchestrator.route_after_classify(state) == "retrieve_memory"


# ── TestClassifyNode ──────────────────────────────────────────────────────────


class TestClassifyNode:
    """Testa o nó de classificação de intenção do agente."""

    async def test_classify_node_returns_reflexion_intent(self, mock_llms):
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.router_chain = MagicMock()
        orchestrator.router_chain.ainvoke = AsyncMock(
            return_value=RouterDecision(intent="reflexion", zona=None, mobiliario=[])
        )

        state = {
            "messages": [HumanMessage(content="O que é Python?")],
            "intent": "",
            "zona": None,
            "mobiliario": [],
        }
        result = await orchestrator.classify_node(state)

        assert result["intent"] == "reflexion"
        assert result["zona"] is None

    async def test_classify_node_returns_arq_intent_with_zona_and_mobiliario(
        self, mock_llms
    ):
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.router_chain = MagicMock()
        orchestrator.router_chain.ainvoke = AsyncMock(
            return_value=RouterDecision(
                intent="arq_extract", zona="quarto", mobiliario=["cama", "guarda-roupa"]
            )
        )

        state = {
            "messages": [
                HumanMessage(
                    content="No quarto com cama e guarda-roupa, a cama encostada na parede"
                )
            ],
            "intent": "",
            "zona": None,
            "mobiliario": [],
        }
        result = await orchestrator.classify_node(state)

        assert result["intent"] == "arq_extract"
        assert result["zona"] == "quarto"
        assert "cama" in result["mobiliario"]

    async def test_classify_node_passes_last_human_message_to_router(self, mock_llms):
        """Apenas a última HumanMessage deve ser enviada ao router."""
        orchestrator = AgentOrchestrator(store=InMemoryStore())
        orchestrator.router_chain = MagicMock()
        orchestrator.router_chain.ainvoke = AsyncMock(
            return_value=RouterDecision(intent="reflexion")
        )

        state = {
            "messages": [
                HumanMessage(content="mensagem anterior"),
                AIMessage(content="resposta anterior"),
                HumanMessage(content="mensagem atual"),
            ],
            "intent": "",
            "zona": None,
            "mobiliario": [],
        }
        await orchestrator.classify_node(state)

        call_args = orchestrator.router_chain.ainvoke.call_args
        message_sent = call_args.args[0]["message"] if call_args.args else call_args.kwargs["message"]
        assert message_sent == "mensagem atual"


# ── TestArqExtractNode ────────────────────────────────────────────────────────


class TestArqExtractNode:
    """Testa o nó de extração de padrões arquitetônicos no contexto do agente."""

    async def test_arq_extract_node_returns_ai_message_with_json_content(
        self, mock_llms
    ):
        orchestrator = AgentOrchestrator(store=InMemoryStore())

        mock_result = ExtrairPadroesResponse(
            zona="quarto",
            mobiliario_valido=["cama"],
            padroes=[
                {
                    "tipo": "restricao",
                    "padrao": "encostado",
                    "objeto": {"nome": "cama"},
                    "lado": "fundos",
                }
            ],
        )

        with patch("app.services.arq_service.arq_service") as mock_service:
            mock_service.extrair_padroes = AsyncMock(return_value=mock_result)

            state = {
                "messages": [HumanMessage(content="A cama encostada na parede")],
                "intent": "arq_extract",
                "zona": "quarto",
                "mobiliario": ["cama"],
            }
            result = await orchestrator.arq_extract_node(state)

        assert len(result["messages"]) == 1
        msg = result["messages"][0]
        assert isinstance(msg, AIMessage)
        assert "encostado" in msg.content

    async def test_arq_extract_node_uses_full_zone_catalog_when_no_mobiliario(
        self, mock_llms
    ):
        """Sem móveis explícitos, usa todas as famílias da zona."""
        orchestrator = AgentOrchestrator(store=InMemoryStore())

        mock_result = ExtrairPadroesResponse(
            zona="quarto", mobiliario_valido=[], padroes=[]
        )

        with patch("app.services.arq_service.arq_service") as mock_service:
            mock_service.extrair_padroes = AsyncMock(return_value=mock_result)

            state = {
                "messages": [HumanMessage(content="A cama encostada")],
                "intent": "arq_extract",
                "zona": "quarto",
                "mobiliario": [],  # nenhum móvel identificado pelo router
            }
            await orchestrator.arq_extract_node(state)

        call_args = mock_service.extrair_padroes.call_args
        request_sent = call_args.args[0] if call_args.args else call_args.kwargs.get("request")
        # Deve ter passado algum mobiliário (do catálogo completo da zona)
        assert len(request_sent.mobiliario) > 0

    async def test_arq_extract_node_returns_error_message_on_exception(
        self, mock_llms
    ):
        """Erro no serviço não deve propagar — retorna mensagem de erro ao usuário."""
        from fastapi import HTTPException

        orchestrator = AgentOrchestrator(store=InMemoryStore())

        with patch("app.services.arq_service.arq_service") as mock_service:
            mock_service.extrair_padroes = AsyncMock(
                side_effect=HTTPException(status_code=422, detail="zona inválida")
            )

            state = {
                "messages": [HumanMessage(content="texto")],
                "intent": "arq_extract",
                "zona": "quarto",
                "mobiliario": ["cama"],
            }
            result = await orchestrator.arq_extract_node(state)

        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert "Erro" in result["messages"][0].content
