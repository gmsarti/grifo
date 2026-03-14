# Implementation Plan - Agentic RAG (Corrective RAG)

This plan outlines the implementation of the Agentic RAG (CRAG) system, integrated as a specialized tool for the Reflexion Agent.

## Architecture Rationale

### Agentic RAG as a Tool
The `Reflexion Agent` (orchestrator) uses the `Agentic RAG` as a tool. This allows the orchestrator to delegate factual queries to a system that knows how to validate documents and perform web search fallbacks.

### Layered Organization
- **Data Source (`/app/data_source`)**: Handles mechanics (ChromaDB, Loaders, Hybrid Search).
- **Processing (`/app/processing/rag/`)**: Handles intelligence and orchestration (Graphs, LLM Chains, Decision Nodes). This keeps the code modular and follows DDD/SDD principles.

## Implementation Backlog

### [PHASE 1] Ingestão e Vector Store
- [x] [TASK-1.1] Implementar `WebIngestionService` no `loaders.py`.
- [x] [TASK-1.2] Configurar `Chroma` e `OpenAIEmbeddings` com busca híbrida (Vector + BM25) no `vector_store.py`.
- [x] [TASK-1.3] Criar script utilitário `scripts/populate_db.py` para popular o vector store.

### [PHASE 2] Infraestrutura do Grafo (app/processing/rag/)
- [x] [TASK-2.1] Criar `app/processing/rag/state.py` com o `GraphState` (question, generation, web_search, documents).
- [x] [TASK-2.2] Implementar chains auxiliares em `app/processing/rag/chains.py`:
    - `retrieval_grader`: LLM com structured output para validar relevância.
    - `rag_generation`: Chain para resposta final baseada no contexto.
    - `question_rewriter`: Para otimizar a busca web caso necessário.

### [PHASE 3] Implementação dos Nós (app/processing/rag/nodes.py)
- [x] [TASK-3.1] Nó `retrieve`: Busca top-3 documentos usando o `HybridRetriever`.
- [x] [TASK-3.2] Nó `grade_documents`: Filtra documentos irrelevantes e define se `web_search` é necessário.
- [x] [TASK-3.3] Nó `web_search`: Integração com Tavily para busca complementar.
- [x] [TASK-3.4] Nó `generate`: Gera a resposta usando os documentos validados.

### [PHASE 4] Orquestração e Integração
- [x] [TASK-4.1] Configurar `StateGraph` em `app/processing/rag/graph.py` com arestas condicionais.
- [x] [TASK-4.2] Criar `app/processing/rag/controller.py` para expor o fluxo como uma interface unificada.
- [x] [TASK-4.3] Registrar o `Agentic RAG` como ferramenta no `app/processing/tools.py`.

### [PHASE 5] Verificação e Observabilidade
- [x] [TASK-5.1] Testes unitários para o `retrieval_grader` em `tests/unit/test_rag_grader.py`.
- [x] [TASK-5.2] Teste de integração do fluxo completo (CRAG tool call).
- [x] [TASK-5.3] Monitoramento via LangSmith e logs estruturados delle etapas de filtragem e recuperação com `timed_process`.
