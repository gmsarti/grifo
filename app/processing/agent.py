import uuid
from contextlib import AsyncExitStack
from typing import Literal

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
from app.processing.tools import AGENT_TOOLS

logger = get_logger(__name__)

# Plan for MAX_ITERATIONS from config or default
MAX_ITERATIONS = getattr(settings, "REFLEXION_MAX_ITERATIONS", 2)


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
        """Creates the LangGraph with checkpointer and store."""
        builder = StateGraph(MessagesState)

        # Add nodes
        builder.add_node("retrieve_memory", self.retrieve_memory_node)
        builder.add_node("draft", self.draft_node)
        builder.add_node("execute_tools", self.reflexion_tools)
        builder.add_node("revise", self.revise_node)
        builder.add_node("extract_knowledge", self.extract_knowledge_node)

        # Define edges
        builder.add_edge(START, "retrieve_memory")
        builder.add_edge("retrieve_memory", "draft")
        builder.add_edge("draft", "execute_tools")
        builder.add_edge("execute_tools", "revise")

        # O ciclo de reflexão agora termina na extração de conhecimento ao invés de END
        builder.add_conditional_edges(
            "revise",
            self.event_loop,
            {
                "execute_tools": "execute_tools",
                "extract_knowledge": "extract_knowledge",
            },
        )
        builder.add_edge("extract_knowledge", END)

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

    async def draft_node(self, state: MessagesState, config=None):
        """Node for the initial draft using the FAST model."""
        with timed_process("Drafting Responder", logger):
            response = await self.first_responder.ainvoke(
                {"messages": state["messages"]}
            )
            return {"messages": [response]}

    async def revise_node(self, state: MessagesState, config=None):
        """Node for revising the answer using the REASONER model."""
        with timed_process("Revision Process", logger):
            response = await self.revisor.ainvoke({"messages": state["messages"]})
            return {"messages": [response]}

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
        self, state: MessagesState
    ) -> Literal["execute_tools", "extract_knowledge"]:
        """Controls the iteration cycle based on tool visits."""
        tool_calls_count = sum(
            1
            for msg in state["messages"][-10:]  # Recent window
            if isinstance(msg, AIMessage) and msg.tool_calls
        )
        return (
            "extract_knowledge"
            if tool_calls_count >= MAX_ITERATIONS
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

        inputs = {"messages": messages}

        # 0. Set Log Context for automatic enrichment
        from app.core.logging import set_log_context

        with set_log_context(
            user_id=user_id, project_id=project_id, thread_id=thread_id
        ):
            # 1. Update short-term history (scoped by project)
            history_db = VectorizedMessageHistory(project_id, thread_id)
            await history_db.add_message(inputs["messages"][0])

            try:
                with get_openai_callback() as cb:
                    with timed_process("Graph Execution", logger):
                        result = await self.graph.ainvoke(inputs, config=config)

                logger.info(
                    "Token usage and tokens details",
                    extra={
                        "tokens": {
                            "total_tokens": cb.total_tokens,
                            "prompt_tokens": cb.prompt_tokens,
                            "completion_tokens": cb.completion_tokens,
                            "total_cost": cb.total_cost,
                        }
                    },
                )

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
                            "usage": {
                                "total_tokens": cb.total_tokens,
                                "prompt_tokens": cb.prompt_tokens,
                                "completion_tokens": cb.completion_tokens,
                                "total_cost": cb.total_cost,
                            },
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
                    "usage": {
                        "total_tokens": cb.total_tokens,
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_cost": cb.total_cost,
                    },
                }
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                return {"error": str(e)}
