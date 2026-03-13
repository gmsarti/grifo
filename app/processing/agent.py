from typing import Literal
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph, MessagesState
from app.core.config import settings
from app.core.llm import get_reasoner, get_fast_model
from app.processing.tools import AGENT_TOOLS
from app.processing.chains import get_first_responder, get_revisor
from app.processing.tool_executor import execute_tools as reflexion_tool_node

# Plan for MAX_ITERATIONS from config or default
MAX_ITERATIONS = getattr(settings, "REFLEXION_MAX_ITERATIONS", 2)


class AgentOrchestrator:
    """
    Orchestrates the Reflexion Agent graph using specialized LLM profiles.
    """

    def __init__(self):
        self.fast_llm = get_fast_model()
        self.reasoner_llm = get_reasoner()
        self.tools = AGENT_TOOLS  # Generic tools (can be used elsewhere)
        self.reflexion_tools = reflexion_tool_node  # Specific tools for Reflexion

        # Initialize chains
        self.first_responder = get_first_responder(self.fast_llm)
        self.revisor = get_revisor(self.reasoner_llm)

        self.graph = self._create_graph()

    def _create_graph(self):
        """Creates the LangGraph for the Reflexion Agent."""
        builder = StateGraph(MessagesState)

        # Add nodes
        builder.add_node("draft", self.draft_node)
        builder.add_node("execute_tools", self.reflexion_tools)
        builder.add_node("revise", self.revise_node)

        # Define edges
        builder.add_edge(START, "draft")
        builder.add_edge("draft", "execute_tools")
        builder.add_edge("execute_tools", "revise")
        builder.add_conditional_edges("revise", self.event_loop, ["execute_tools", END])

        return builder.compile()

    async def draft_node(self, state: MessagesState):
        """Node for the initial draft using the FAST model."""
        response = await self.first_responder.ainvoke({"messages": state["messages"]})
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

    async def process_message(self, message: str, thread_id: str = None) -> str:
        """Processes a user message through the graph."""
        config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
        inputs = {"messages": [HumanMessage(content=message)]}
        try:
            result = await self.graph.ainvoke(inputs, config=config)
            if "messages" in result and len(result["messages"]) > 0:
                # Return the content of the last AI message
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        return msg.content
            return "No response generated."
        except Exception as e:
            return f"Error processing message: {str(e)}"
