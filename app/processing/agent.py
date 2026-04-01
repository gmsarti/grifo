import operator
import uuid
from contextlib import AsyncExitStack, nullcontext
from typing import Annotated, Literal

from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.sqlite.aio import AsyncSqliteStore

from app.core.config import settings
from app.core.llm import get_fast_model, get_reasoner
from app.core.logging import get_logger, timed_process
from app.processing.chains import (
    get_first_responder,
    get_knowledge_extractor,
    get_revisor,
)
from app.processing.memory import StoreMemoryManager, VectorizedMessageHistory
from app.processing.router_chain import get_router_chain
from app.processing.tools import AGENT_TOOLS

logger = get_logger(__name__)

# Plan for MAX_ITERATIONS from config or default
MAX_ITERATIONS = getattr(settings, "REFLEXION_MAX_ITERATIONS", 2)

# Providers that support cost tracking via LangChain callbacks
_PROVIDERS_WITH_COST_TRACKING = {"openai"}


class ReflexionState(MessagesState):
    """Estado do grafo com roteamento, extração arquitetônica e reflexão."""

    iteration_count: Annotated[int, operator.add]
    # Campos preenchidos pelo nó classify — usados para roteamento e extração arq.
    intent: str          # "reflexion" | "arq_extract"
    zona: str | None     # zona identificada pelo router, ou None
    mobiliario: list[str]  # móveis identificados pelo router


def _extract_usage_from_messages(messages: list) -> dict:
    """Extrai tokens de uso dos AIMessages via usage_metadata (agnóstico de provider)."""
    prompt_tokens = 0
    completion_tokens = 0
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.usage_metadata:
            prompt_tokens += msg.usage_metadata.get("input_tokens", 0)
            completion_tokens += msg.usage_metadata.get("output_tokens", 0)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


@tool
def answer_question_tool(answer: str, reflection: dict, search_queries: list[str]):
    """Tool para AnswerQuestion"""
    return {
        "answer": answer,
        "reflection": reflection,
        "search_queries": search_queries,
    }


@tool
def revise_answer_tool(
    answer: str, reflection: dict, search_queries: list[str], references: list[str]
):
    """Tool para ReviseAnswer"""
    return {
        "answer": answer,
        "reflection": reflection,
        "search_queries": search_queries,
        "references": references,
    }


class AgentOrchestrator:
    """
    Orchestrates the Reflexion Agent graph using specialized LLM profiles
    and advanced memory management (Short-term vectorized + Long-term store).
    Includes observability (LangSmith) and cost tracking.
    """

    def __init__(self, store: AsyncSqliteStore | None = None):
        self.fast_llm = get_fast_model()
        self.reasoner_llm = get_reasoner()
        self.tools = AGENT_TOOLS
        self.reflexion_tools = ToolNode([answer_question_tool, revise_answer_tool])

        # State managed lazily in _ensure_initialized
        self.store = store
        self._exit_stack = AsyncExitStack()
        self.checkpointer = None
        self.store_manager = StoreMemoryManager(store) if store else None
        self.graph = None

        # Initialize chains
        self.first_responder = get_first_responder(self.fast_llm)
        self.revisor = get_revisor(self.reasoner_llm)
        self.knowledge_extractor = get_knowledge_extractor(self.fast_llm)
        self.router_chain = get_router_chain()

    async def _ensure_initialized(self):
        """Lazily initializes async persistent components and compiles the graph."""
        if self.graph is not None:
            return

        import os

        db_dir = os.path.dirname(settings.MEMORY_DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Persistent components (Managed by AsyncExitStack to ensure proper lifecycle)
        if self.checkpointer is None:
            self.checkpointer = await self._exit_stack.enter_async_context(
                AsyncSqliteSaver.from_conn_string(settings.MEMORY_DB_PATH)
            )

        if self.store is None:
            self.store = await self._exit_stack.enter_async_context(
                AsyncSqliteStore.from_conn_string(settings.MEMORY_DB_PATH)
            )
            await self.store.setup()
            self.store_manager = StoreMemoryManager(self.store)

        self.graph = self._create_graph()

    async def close(self):
        """Closes all persistent stores and released resources."""
        await self._exit_stack.aclose()
        self.checkpointer = None
        self.store = None
        self.graph = None

    def _create_graph(self):
        """Creates the LangGraph with router, reflexion loop, and arq extractor."""
        builder = StateGraph(ReflexionState)

        # Add nodes
        builder.add_node("classify", self.classify_node)
        builder.add_node("retrieve_memory", self.retrieve_memory_node)
        builder.add_node("draft", self.draft_node)
        builder.add_node("execute_tools", self.reflexion_tools)
        builder.add_node("revise", self.revise_node)
        builder.add_node("extract_knowledge", self.extract_knowledge_node)
        builder.add_node("arq_extract", self.arq_extract_node)

        # Router: classify first, then branch
        builder.add_edge(START, "classify")
        builder.add_conditional_edges(
            "classify",
            self.route_after_classify,
            {
                "retrieve_memory": "retrieve_memory",
                "arq_extract": "arq_extract",
            },
        )

        # Reflexion loop
        builder.add_edge("retrieve_memory", "draft")
        builder.add_edge("draft", "execute_tools")
        builder.add_edge("execute_tools", "revise")
        builder.add_conditional_edges(
            "revise",
            self.event_loop,
            {
                "execute_tools": "execute_tools",
                "extract_knowledge": "extract_knowledge",
            },
        )
        builder.add_edge("extract_knowledge", END)

        # Arq extractor path
        builder.add_edge("arq_extract", END)

        return builder.compile(checkpointer=self.checkpointer, store=self.store)

    async def retrieve_memory_node(self, state: MessagesState, config):
        """
        Retrieves relevant context from vectorized history and long-term store.
        (Timed process for observability)
        """
        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id", "default")
        user_id = configurable.get("user_id", "default_user")
        project_id = configurable.get("project_id", "default_project")

        last_message = state["messages"][-1].content if state["messages"] else ""

        with timed_process("Memory Retrieval", logger):
            context_parts = []

            # 1. Short-term Vectorized History (Scoped by project)
            history_db = VectorizedMessageHistory(project_id, thread_id)
            hist_context = history_db.search_history(last_message)
            if hist_context:
                context_parts.append(f"Relevant Conversation History:\n{hist_context}")

            # 2. Long-term Store (Cross-session)
            memories = await self.store_manager.search_memories(user_id, last_message)
            if memories:
                mem_text = "\n".join([f"- {m.value['content']}" for m in memories])
                context_parts.append(f"Known Facts/Preferences:\n{mem_text}")

            if context_parts:
                from langchain_core.messages import SystemMessage

                combined_context = "\n\n".join(context_parts)
                memory_msg = SystemMessage(
                    content=f"Context from memory:\n{combined_context}",
                    name="memory_context",
                )
                return {"messages": [memory_msg]}

        return {"messages": []}

    async def classify_node(self, state: ReflexionState, config=None):
        """
        Classifica a intenção da mensagem e extrai zona/mobiliário se for arq_extract.
        Usa o modelo rápido — não exige raciocínio avançado.
        """
        last_human = next(
            (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            None,
        )
        message = last_human.content if last_human else ""

        with timed_process("Intent Classification", logger):
            decision = await self.router_chain.ainvoke({"message": message})

        logger.info(
            "Router decision: intent=%s zona=%s mobiliario=%s",
            decision.intent,
            decision.zona,
            decision.mobiliario,
        )
        return {
            "intent": decision.intent,
            "zona": decision.zona,
            "mobiliario": decision.mobiliario,
        }

    def route_after_classify(
        self, state: ReflexionState
    ) -> Literal["retrieve_memory", "arq_extract"]:
        """
        Roteia para arq_extract se a intenção for extração arquitetônica E uma zona
        tiver sido identificada. Sem zona, cai no reflexion (o LLM pode pedir mais
        contexto ao usuário).
        """
        if state.get("intent") == "arq_extract" and state.get("zona"):
            return "arq_extract"
        return "retrieve_memory"

    async def arq_extract_node(self, state: ReflexionState, config=None):
        """
        Invoca o pipeline de extração de padrões arquitetônicos e devolve o resultado
        como mensagem do assistente em JSON formatado.

        Se nenhum mobiliário foi identificado pelo router, usa todos os móveis da zona.
        """
        import json

        from fastapi import HTTPException

        from app.data.arq_vocabulary import OBJETOS_POR_ZONA
        from app.schemas.arq_schemas import ExtrairPadroesRequest
        from app.services.arq_service import arq_service

        zona = state["zona"]
        mobiliario = state.get("mobiliario") or []

        # Fallback: usa todas as famílias da zona se nenhum móvel foi identificado
        if not mobiliario:
            mobiliario = list(OBJETOS_POR_ZONA.get(zona, {}).keys())

        last_human = next(
            (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            None,
        )
        texto = last_human.content if last_human else ""

        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id", "default_user")
        thread_id = configurable.get("user_thread_id", "default")

        with timed_process("Arq Pattern Extraction", logger):
            try:
                request = ExtrairPadroesRequest(
                    zona=zona, mobiliario=mobiliario, texto=texto
                )
                result = await arq_service.extrair_padroes(request)
                from app.processing.arq_text_converter import padroes_para_markdown
                response_content = padroes_para_markdown(
                    result.padroes,
                    zona=result.zona,
                    mobiliario=result.mobiliario_valido,
                )
                if result.padroes and self.store_manager:
                    await self._save_arq_patterns_to_memory(
                        user_id=user_id,
                        thread_id=thread_id,
                        zona=zona,
                        mobiliario=mobiliario,
                        padroes=result.padroes,
                    )
            except HTTPException as e:
                response_content = f"Erro na extração de padrões: {e.detail}"
            except Exception as e:
                logger.exception("arq_extract_node: erro inesperado")
                response_content = f"Erro inesperado na extração de padrões: {e}"

        return {"messages": [AIMessage(content=response_content)]}

    async def _save_arq_patterns_to_memory(
        self,
        user_id: str,
        thread_id: str,
        zona: str,
        mobiliario: list[str],
        padroes: list[dict],
    ) -> None:
        """
        Persiste os padrões extraídos na memória de longo prazo do usuário.

        Armazena uma entrada por chamada de extração, com descrição legível
        (para busca semântica) e o JSON completo dos padrões (para recuperação
        estruturada futura). Entradas anteriores da mesma zona não são
        sobrescritas — acumulam-se como histórico de decisões.
        """
        import json

        mobiliario_str = ", ".join(mobiliario)
        pattern_types = ", ".join(
            p.get("padrao", p.get("tipo", "desconhecido")) for p in padroes
        )
        fact_content = (
            f"[Layout Arquitetônico] "
            f"Zona: {zona}. "
            f"Mobiliário: {mobiliario_str}. "
            f"{len(padroes)} padrão(ões) definido(s) ({pattern_types}). "
            f"JSON: {json.dumps(padroes, ensure_ascii=False)}"
        )
        fact_key = f"arq_{zona}_{uuid.uuid4().hex[:8]}"
        try:
            await self.store_manager.save_fact(
                user_id, fact_key, fact_content, thread_id=thread_id
            )
            logger.info(
                "Arq patterns saved to memory: zona=%s patterns=%d user=%s",
                zona,
                len(padroes),
                user_id,
            )
        except Exception:
            logger.exception("Falha ao salvar padrões arq na memória de longo prazo")

    async def draft_node(self, state: MessagesState, config=None):
        """Node for the initial draft using the FAST model."""
        with timed_process("Drafting Responder", logger):
            response = await self.first_responder.ainvoke(
                {"messages": state["messages"]}
            )
            return {"messages": [response]}

    async def revise_node(self, state: ReflexionState, config=None):
        """Node for revising the answer using the REASONER model."""
        with timed_process("Revision Process", logger):
            response = await self.revisor.ainvoke({"messages": state["messages"]})
            return {"messages": [response], "iteration_count": 1}

    async def extract_knowledge_node(
        self, state: MessagesState, config: RunnableConfig | None = None
    ):
        """
        Node final que extrai fatos relevantes da interação atual e os
        salva na memória de longo prazo (StoreMemoryManager).
        """
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id", "default_user")
        thread_id = configurable.get("user_thread_id", "default")

        with timed_process("Knowledge Extraction", logger):
            # Obtém as últimas interações (usuário + reflexão + IA)
            recent_messages = state["messages"][-6:]
            history_lines = []

            for m in recent_messages:
                if isinstance(m, HumanMessage):
                    history_lines.append(f"Usuário: {m.content}")
                elif isinstance(m, AIMessage):
                    if m.content:
                        history_lines.append(f"IA: {m.content}")
                    elif m.tool_calls:
                        # A resposta fica em tool_calls[].args["answer"] (AnswerQuestion/ReviseAnswer)
                        for tc in m.tool_calls:
                            answer = tc.get("args", {}).get("answer")
                            if answer:
                                history_lines.append(f"IA: {answer}")
                                break

            history_str = "\n".join(history_lines)

            if history_str:
                try:
                    extraction = await self.knowledge_extractor.ainvoke(
                        {"history": history_str}
                    )
                    if extraction and hasattr(extraction, "facts") and extraction.facts:
                        for item in extraction.facts:
                            fact_key = f"fact_{uuid.uuid4().hex[:8]}"
                            formatted_fact = f"[{item.topic}] {item.fact}"

                            # Salva o aprendizado permanentemente no namespace do usuário
                            await self.store_manager.save_fact(
                                user_id, fact_key, formatted_fact, thread_id=thread_id
                            )
                            logger.info(
                                f"Learned new fact for user {user_id}: {formatted_fact}"
                            )
                except Exception as e:
                    logger.error(f"Error extracting knowledge: {str(e)}")

        return {"messages": []}  # Não polui as mensagens da sessão principal

    def event_loop(
        self, state: ReflexionState
    ) -> Literal["execute_tools", "extract_knowledge"]:
        """Controls the iteration cycle using the explicit iteration counter."""
        return (
            "extract_knowledge"
            if state.get("iteration_count", 0) >= MAX_ITERATIONS
            else "execute_tools"
        )

    async def process_message(
        self,
        message: str,
        thread_id: str,
        project_id: str,
        user_id: str = "default_user",
        system_prompt: str | None = None,
    ) -> dict:
        """Processes a user message through the graph with monitoring."""
        await self._ensure_initialized()

        # Usa um ID único por invocação no checkpointer para evitar que o
        # MemorySaver acumule tool_calls sem ToolMessages entre chamadas distintas.
        # A memória cross-turn é gerenciada pelo VectorizedMessageHistory.
        invocation_id = f"{thread_id}_{uuid.uuid4().hex}"

        config = {
            "configurable": {
                "thread_id": invocation_id,
                "user_thread_id": thread_id,  # thread real do usuário para memória
                "user_id": user_id,
                "project_id": project_id,
            },
            "metadata": {
                "thread_id": thread_id,
                "user_id": user_id,
                "project_id": project_id,
            },
        }

        from langchain_core.messages import SystemMessage

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))

        inputs = {
            "messages": messages,
            # Campos do router — preenchidos pelo nó classify, inicializados aqui
            # para satisfazer o TypedDict do estado do LangGraph.
            "intent": "reflexion",
            "zona": None,
            "mobiliario": [],
        }

        # 0. Set Log Context for automatic enrichment
        from app.core.logging import set_log_context

        with set_log_context(
            user_id=user_id, project_id=project_id, thread_id=thread_id
        ):
            # 1. Update short-term history (scoped by project)
            history_db = VectorizedMessageHistory(project_id, thread_id)
            await history_db.add_message(inputs["messages"][0])

            try:
                provider = settings.MODEL_PROVIDER
                if provider in _PROVIDERS_WITH_COST_TRACKING:
                    cost_ctx = get_openai_callback()
                else:
                    logger.warning(
                        "Cost tracking unavailable for provider '%s'. "
                        "total_cost will be null.",
                        provider,
                    )
                    cost_ctx = nullcontext()

                with cost_ctx as cb:
                    with timed_process("Graph Execution", logger):
                        result = await self.graph.ainvoke(inputs, config=config)

                if provider in _PROVIDERS_WITH_COST_TRACKING:
                    usage = {
                        "total_tokens": cb.total_tokens,
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_cost": cb.total_cost,
                    }
                else:
                    usage = {
                        **_extract_usage_from_messages(result.get("messages", [])),
                        "total_cost": None,
                    }

                logger.info("Token usage", extra={"tokens": usage})

                # Extract final AI Message and update history
                if "messages" in result and len(result["messages"]) > 0:
                    final_answer = None
                    final_ai_msg = None

                    # The LLM is forced to use AnswerQuestion/ReviseAnswer tools,
                    # so the answer lives in tool_calls[].args["answer"], not in content.
                    for msg in reversed(result["messages"]):
                        if not (
                            isinstance(msg, AIMessage)
                            or type(msg).__name__ == "AIMessage"
                        ):
                            continue
                        # Prefer plain content (fallback path)
                        if msg.content:
                            final_answer = msg.content
                            final_ai_msg = msg
                            break
                        # Extract answer from tool call args
                        if msg.tool_calls:
                            args = msg.tool_calls[0].get("args", {})
                            if "answer" in args:
                                final_answer = args["answer"]
                                final_ai_msg = msg  # noqa: F841
                                break

                    if final_answer is not None:
                        answer_msg = AIMessage(content=final_answer)
                        await history_db.add_message(answer_msg)

                        # Extract grounding metadata from ToolMessages
                        grounding = {
                            "local_sources": [],
                            "web_sources": [],
                            "search_queries": [],
                        }
                        import json

                        for msg in result["messages"]:
                            if isinstance(msg, ToolMessage):
                                try:
                                    tool_res = json.loads(msg.content)
                                    if isinstance(tool_res, dict):
                                        docs = tool_res.get("documents", [])
                                        for d in docs:
                                            source = d.get("metadata", {}).get(
                                                "source", "unknown"
                                            )
                                            if (
                                                source == "web_search"
                                                or source.startswith("http")
                                            ):
                                                grounding["web_sources"].append(source)
                                            else:
                                                grounding["local_sources"].append(
                                                    source
                                                )
                                    if "query" in tool_res:
                                        grounding["search_queries"].append(
                                            tool_res["query"]
                                        )
                                except (json.JSONDecodeError, TypeError):
                                    continue

                        return {
                            "response": final_answer,
                            "project_id": project_id,
                            "thread_id": thread_id,
                            "iterations": sum(
                                1
                                for m in result["messages"]
                                if isinstance(m, ToolMessage)
                            ),
                            "grounding_metadata": grounding,
                            "usage": usage,
                            "process_trace": [
                                m.name if hasattr(m, "name") and m.name else "msg"
                                for m in result["messages"]
                            ],
                        }

                return {
                    "response": "No response generated.",
                    "project_id": project_id,
                    "thread_id": thread_id,
                    "iterations": 0,
                    "grounding_metadata": {
                        "local_sources": [],
                        "web_sources": [],
                        "search_queries": [],
                    },
                    "process_trace": [],
                    "usage": usage,
                }
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                return {"error": str(e)}
