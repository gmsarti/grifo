# Reflexion Agent Replication Guide

This guide provides the steps to replicate the Reflexion Agent in a new repository.

## Step 1: Initialization
1. Create a new directory and initialize a Python project.
2. Install the necessary packages:
   ```bash
   pip install langchain langgraph langchain-openai langchain-tavily python-dotenv
   ```
3. Set up your `.env` file:
   ```bash
   OPENAI_API_KEY=your_key_here
   TAVILY_API_KEY=your_key_here
   ```

## Step 2: Component Implementation Order
1. **`schemas.py`**: Start by defining the Pydantic models. This ensures structural consistency for tool calling.
2. **`tool_executor.py`**: Set up the `TavilySearch` tool. Wrap it in a `ToolNode` so LangGraph can manage the execution automatically.
3. **`chains.py`**: Build your LCEL chains. 
   - Use `.partial()` to inject specific instructions for the draft and revision phases.
   - Use `.bind_tools()` to force the LLM to output according to your schemas.
4. **`main.py`**:
   - Define your nodes using the chains created.
   - Assemble the graph using `StateGraph(MessagesState)`.
   - Implement the `event_loop` to count `ToolMessage` items and enforce the iteration limit.

## Step 3: Execution
To run the agent, simply invoke the workflow with a user message:
```python
res = workflow.invoke({"messages": [{"role": "user", "content": "Your query here"}]})
print(res["messages"][-1].content)
```

## Pro-Tips for SDD
- **Test Individual Chains**: Before building the graph, test `first_responder` and `revisor` independently to ensure they return the expected schemas.
- **Trace with LangSmith**: Set `LANGSMITH_API_KEY` to visualize the logic flow and the transitions between draft, tools, and revision.
