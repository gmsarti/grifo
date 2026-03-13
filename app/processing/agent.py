from typing import Literal, Optional
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, BaseMessage
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from app.core.config import settings
from app.core.llm import get_reasoner, get_fast_model
from app.processing.tools import AGENT_TOOLS
from app.processing.chains import get_first_responder, get_revisor
from app.processing.tool_executor import execute_tools as reflexion_tool_node
from app.processing.memory import VectorizedMessageHistory, StoreMemoryManager

# Plan for MAX_ITERATIONS from config or default
MAX_ITERATIONS = getattr(settings, "REFLEXION_MAX_ITERATIONS", 2)


class AgentOrchestrator:
    """
    Orchestrates the Reflexion Agent graph using specialized LLM profiles
    and advanced memory management (Short-term vectorized + Long-term store).
    """

    def __init__(self, store: Optional[InMemoryStore] = None):
        self.fast_llm = get_fast_model()
        self.reasoner_llm = get_reasoner()
        self.tools = AGENT_TOOLS
        self.reflexion_tools = reflexion_tool_node
        
        # Memory Components
        self.checkpointer = MemorySaver()
        self.store = store or InMemoryStore()
        self.store_manager = StoreMemoryManager(self.store)

        # Initialize chains
        self.first_responder = get_first_responder(self.fast_llm)
        self.revisor = get_revisor(self.reasoner_llm)

        self.graph = self._create_graph()

    def _create_graph(self):
        """Creates the LangGraph with checkpointer and store."""
        builder = StateGraph(MessagesState)

        # Add nodes
        builder.add_node("retrieve_memory", self.retrieve_memory_node)
        builder.add_node("draft", self.draft_node)
        builder.add_node("execute_tools", self.reflexion_tools)
        builder.add_node("revise", self.revise_node)

        # Define edges
        builder.add_edge(START, "retrieve_memory")
        builder.add_edge("retrieve_memory", "draft")
        builder.add_edge("draft", "execute_tools")
        builder.add_edge("execute_tools", "revise")
        builder.add_conditional_edges("revise", self.event_loop, ["execute_tools", END])

        return builder.compile(checkpointer=self.checkpointer, store=self.store)

    async def retrieve_memory_node(self, state: MessagesState, config: dict):
        """
        TASK-4.1 & 4.3: Retrieves relevant context from vectorized history
        and long-term store based on the last user message.
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        context_parts = []
        
        # 1. Short-term Vectorized History
        history_db = VectorizedMessageHistory(thread_id)
        hist_context = history_db.search_history(last_message)
        if hist_context:
            context_parts.append(f"Relevant Conversation History:\n{hist_context}")
            
        # 2. Long-term Store (Cross-session)
        # Assuming user_id is passed in config or derived from thread_id
        user_id = config.get("configurable", {}).get("user_id", "default_user")
        memories = await self.store_manager.search_memories(user_id, last_message)
        if memories:
            mem_text = "\n".join([f"- {m.value['content']}" for m in memories])
            context_parts.append(f"Known Facts/Preferences:\n{mem_text}")
            
        if context_parts:
            # We inject this context as a system message or a prepend to the prompt
            # For simplicity, we add a SystemMessage with context
            from langchain_core.messages import SystemMessage
            combined_context = "\n\n".join(context_parts)
            memory_msg = SystemMessage(
                content=f"Context from memory:\n{combined_context}",
                name="memory_context"
            )
            return {"messages": [memory_msg]}
        
        return {"messages": []}

    async def draft_node(self, state: MessagesState):
        """Node for the initial draft using the FAST model."""
        response = await self.first_responder.ainvoke({"messages": state["messages"]})
        
        # Update vectorized history with user message and response
        # (This could also be done in a separate edge or listener)
        return {"messages": [response]}

    async def revise_node(self, state: MessagesState):
        """Node for revising the answer using the REASONER model."""
        response = await self.revisor.ainvoke({"messages": state["messages"]})
        return {"messages": [response]}

    def event_loop(self, state: MessagesState) -> Literal["execute_tools", "__end__"]:
        """Controls the iteration cycle based on tool visits."""
        count_tool_visits = sum(
            isinstance(item, ToolMessage) for item in state["messages"]
        )
        if count_tool_visits >= MAX_ITERATIONS:
            return END
        return "execute_tools"

    async def process_message(self, message: str, thread_id: str = None, user_id: str = None) -> str:
        """Processes a user message through the graph."""
        thread_id = thread_id or "default"
        user_id = user_id or "default_user"
        
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        inputs = {"messages": [HumanMessage(content=message)]}
        
        # Update short-term history with the new user message
        history_db = VectorizedMessageHistory(thread_id)
        await history_db.add_message(inputs["messages"][0])
        
        try:
            result = await self.graph.ainvoke(inputs, config=config)
            
            # Extract final AI Message and update history
            if "messages" in result and len(result["messages"]) > 0:
                final_ai_msg = None
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        final_ai_msg = msg
                        break
                
                if final_ai_msg:
                    await history_db.add_message(final_ai_msg)
                    return final_ai_msg.content
                    
            return "No response generated."
        except Exception as e:
            return f"Error processing message: {str(e)}"
