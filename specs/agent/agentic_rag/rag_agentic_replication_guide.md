# RAG Agentic Replication Guide

This guide details how to set up and replicate the RAG Agentic (Corrective RAG) infrastructure.

## Step 1: Data Ingestion Setup
1. Define your data sources (URLs) in `ingestion.py`.
2. Configure the `Chroma` vector store with `OpenAIEmbeddings`.
3. Run the ingestion script once to populate the `./.chroma_db` directory.

## Step 2: Grader Chain Implementation
1. Create `graph/chains/retrieval_grader.py`.
2. Use `llm.with_structured_output(GradeDocuments)` to ensure the grader returns a simple `yes` or `no`.
3. Test the grader with known relevant and irrelevant document snippets.

## Step 3: Graph Construction Order
1. **Define State**: Use `TypedDict` in `graph/state.py` to ensure all nodes share a consistent data structure.
2. **Implement Nodes**:
   - `retrieve`: Fetch docs from the vector store.
   - `grade_documents`: Iterate through docs using the `retrieval_grader`. If a doc is irrelevant, set `web_search = True`.
3. **Assemble Workflow**: In `graph/graph.py`, use `StateGraph` to link nodes. Use `add_conditional_edges` to route to Web Search if the `web_search` flag is set.

## Step 4: Environment Variables
Ensure the following are in your `.env`:
```bash
OPENAI_API_KEY=...
TAVILY_API_KEY=... # Required for the fallback web search
```

## Pro-Tips for SDD
- **Modular Retrieval**: Keep the `retriever` instance in a central location (`ingestion.py`) so both the stand-alone ingestion and the graph nodes can use it.
- **Trace Ingestion**: Use `langchain.debug = True` during initial ingestion to verify chunking and embedding generation.
