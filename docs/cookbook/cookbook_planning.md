# Cookbook — Planejamento

Guias práticos e reutilizáveis derivados do projeto Grifo.
Cada história representa um cookbook independente. As tarefas são os blocos de construção do documento.

Convenção de marcação: `[ ]` pendente · `[x]` concluído

---

## História 1 — Suite de Testes para AI Agents

> **Como** desenvolvedor Python que vai construir um agente com LangGraph e FastAPI,
> **quero** um guia prático de como estruturar a suite de testes,
> **para que** eu parta de uma base sólida sem precisar descobrir armadilhas de asyncio, fixtures e mocks de LLM na tentativa e erro.

Arquivo alvo: `docs/cookbook/testing_ai_agents.md`

- [ ] **H1.T1** Seção: princípios e estrutura de diretórios (`unit/`, `integration/`, `web/`) — quando usar cada camada
- [ ] **H1.T2** Seção: configuração do `pytest.ini` para projetos async — `asyncio_mode = auto`, `asyncio_default_test_loop_scope = session`, por que `session` resolve o `RuntimeError: Event loop is closed` do `AsyncSqliteStore`
- [ ] **H1.T3** Seção: hierarquia de `conftest.py` — global, por camada, por subdiretório; regra de resolução do pytest (ancestor-first)
- [ ] **H1.T4** Seção: fixture `client` async (`AsyncClient` + `ASGITransport`) e por que abandonar `TestClient` síncrono
- [ ] **H1.T5** Seção: mocks de LLM — padrão `MagicMock + AsyncMock` para chains LangChain, como mockar `get_first_responder` / `get_revisor` via `patch`
- [ ] **H1.T6** Seção: mock de `VectorStoreManager` — patching de `Chroma + OpenAIEmbeddings + HybridRetriever`; caso especial do `HybridRetriever` (Pydantic) que impede fixture global
- [ ] **H1.T7** Seção: `dependency_overrides` — sempre em fixtures com `yield` + `.pop()`, nunca no corpo do teste
- [ ] **H1.T8** Seção: marker `prompt_contract` — isolar testes frágeis de conteúdo de prompt; `pytest -m "not prompt_contract"` para runs rápidos
- [ ] **H1.T9** Seção: fixtures de banco de dados — `db_session` async com rollback por teste; fixture `test_user` / `test_project` com email único via uuid

---

## História 2 — Reflexion Agent com LangGraph

> **Como** desenvolvedor que quer implementar um agente com auto-crítica e refinamento iterativo,
> **quero** um guia passo a passo do padrão Reflexion usando LangGraph,
> **para que** eu entenda como montar o grafo, definir os schemas de tool_call e controlar o loop de revisão.

Arquivo alvo: `docs/cookbook/reflexion_agent.md`

- [ ] **H2.T1** Seção: o que é Reflexion — ciclo draft → critique → revise, diferença para um agente ReAct simples
- [ ] **H2.T2** Seção: schemas Pydantic para tool_calls — `AnswerQuestion` (answer, reflection, search_queries), `ReviseAnswer` (answer, references, missing, superfluous), por que usar `tool_choice` forçado
- [ ] **H2.T3** Seção: montagem do `StateGraph` — nós (`retrieve_memory`, `draft`, `execute_tools`, `revise`, `extract_knowledge`), arestas condicionais, controle de iterações com `MAX_ITERATIONS`
- [ ] **H2.T4** Seção: LLMs especializados — modelo rápido para draft (gpt-4o-mini), modelo reasoner para revisão (gpt-4o); como injetar via fábrica
- [ ] **H2.T5** Seção: integração de ferramentas no grafo — `ToolNode`, como o agente emite `search_queries` e como o nó de tools as executa
- [ ] **H2.T6** Seção: lifecycle do `AgentOrchestrator` — `AsyncExitStack`, `AsyncSqliteStore` como backend de memória de longo prazo, inicialização única via `Depends()`
- [ ] **H2.T7** Seção: observabilidade — callbacks OpenAI para tracking de tokens, integração com LangSmith, logging estruturado por requisição

---

## História 3 — Corrective RAG (CRAG) com LangGraph

> **Como** desenvolvedor que precisa de RAG confiável mesmo quando a base de conhecimento local é insuficiente,
> **quero** um guia do padrão CRAG com roteamento condicional,
> **para que** eu saiba como avaliar documentos recuperados e acionar busca web como fallback automático.

Arquivo alvo: `docs/cookbook/corrective_rag.md`

- [ ] **H3.T1** Seção: o problema que o CRAG resolve — RAG ingênuo retorna lixo quando os docs não cobrem a pergunta; grading como solução
- [ ] **H3.T2** Seção: `GraphState` — campos `question`, `generation`, `web_search`, `documents`; por que usar `TypedDict` e não dataclass
- [ ] **H3.T3** Seção: nó `retrieve` — `VectorStoreManager.as_retriever()`, hybrid search, escopo por `project_id`
- [ ] **H3.T4** Seção: nó `grade_documents` — chain de relevance grading com saída binária (`yes`/`no`), lógica de decisão `web_search = True/False`
- [ ] **H3.T5** Seção: nó `web_search` — integração com Tavily, reformat de resultados para o estado do grafo
- [ ] **H3.T6** Seção: nó `generate` — prompt com contexto filtrado, evitar alucinação com docs irrelevantes descartados
- [ ] **H3.T7** Seção: arestas condicionais — `decide_to_generate` baseado no estado `web_search`; diagrama do fluxo completo
- [ ] **H3.T8** Seção: exposição como ferramenta do agente — como o `AgentOrchestrator` invoca o CRAG via tool call

---

## História 4 — Hybrid Retrieval: Vector + BM25 + RRF

> **Como** desenvolvedor montando um sistema de busca sobre documentos,
> **quero** entender como combinar busca semântica e busca lexical,
> **para que** eu não dependa apenas de embeddings e não perca resultados exatos que o vetor não recupera bem.

Arquivo alvo: `docs/cookbook/hybrid_retrieval.md`

- [ ] **H4.T1** Seção: por que hybrid — limitações de vector-only (paráfrases sem embeddings similares) e BM25-only (sem semântica); quando cada um ganha
- [ ] **H4.T2** Seção: setup do `VectorStoreManager` — `Chroma` com `OpenAIEmbeddings`, scoping por `project_id` (collection separada por projeto)
- [ ] **H4.T3** Seção: `BM25Retriever` com persistência — reconstrução do índice a partir dos docs do Chroma na inicialização; por que não persiste o índice direto
- [ ] **H4.T4** Seção: `HybridRetriever` — implementação do `BaseRetriever`, como combinar listas de docs das duas fontes
- [ ] **H4.T5** Seção: Reciprocal Rank Fusion (RRF) — algoritmo, parâmetro `k`, por que é robusto mesmo sem calibrar pesos
- [ ] **H4.T6** Seção: ingestão multi-formato — `FileIngestionService` (PDF, DOCX, CSV, TXT, MD), `WebIngestionService` (URL), chunking com `RecursiveCharacterTextSplitter`
- [ ] **H4.T7** Seção: rebuild do BM25 após ingestão — quando chamar `rebuild_bm25`, thread-safety em ambiente async

---

## História 5 — Dual Memory: Curto e Longo Prazo

> **Como** desenvolvedor construindo um agente que deve lembrar o usuário entre sessões,
> **quero** um guia do sistema de memória em duas camadas,
> **para que** eu entenda como separar contexto de conversa (curto prazo) de fatos aprendidos (longo prazo) e como o agente acessa ambos.

Arquivo alvo: `docs/cookbook/dual_memory.md`

- [ ] **H5.T1** Seção: visão geral das duas camadas — `VectorizedMessageHistory` (curto prazo, por thread) vs `StoreMemoryManager` (longo prazo, por usuário); quando cada uma é consultada
- [ ] **H5.T2** Seção: `VectorizedMessageHistory` — armazenamento no ChromaDB, `search_history()` por similaridade, escopo `project_id + thread_id`
- [ ] **H5.T3** Seção: `StoreMemoryManager` e `AsyncSqliteStore` — namespaces `(user_id, thread_id)`, `asearch` por similaridade semântica, `aput` para persistir fatos
- [ ] **H5.T4** Seção: extração automática de fatos — `KnowledgeExtraction` schema, `get_knowledge_extractor` chain, quando disparar (fim de turno), anti-especulação no prompt
- [ ] **H5.T5** Seção: injeção de memória no prompt — como o nó `retrieve_memory_node` monta o contexto com histórico + fatos para o `draft_node`
- [ ] **H5.T6** Seção: isolamento de escopo — por que `user_id` no namespace de longo prazo evita vazamento entre usuários; project scoping para short-term

---

## História 6 — FastAPI Assíncrono com LangGraph

> **Como** desenvolvedor integrando LangGraph em uma API FastAPI,
> **quero** um guia dos padrões de dependency injection e lifecycle management,
> **para que** eu inicialize recursos pesados (grafos, stores, vector DBs) uma única vez e os sirva eficientemente.

Arquivo alvo: `docs/cookbook/fastapi_langgraph.md`

- [ ] **H6.T1** Seção: problema dos recursos pesados — `AgentOrchestrator` e `VectorStoreManager` não podem ser recriados por request; custo de inicialização
- [ ] **H6.T2** Seção: lifespan do FastAPI — `@asynccontextmanager` para inicializar e destruir recursos; `app.state` como container
- [ ] **H6.T3** Seção: `Depends()` para singletons — `get_orchestrator()`, `get_vector_store()` como factories que retornam instâncias do `app.state`
- [ ] **H6.T4** Seção: `AsyncExitStack` no `AgentOrchestrator` — gerenciar múltiplos context managers async (`AsyncSqliteStore`) sem vazar recursos
- [ ] **H6.T5** Seção: `dependency_overrides` em testes — padrão de substituição em fixtures com `yield` + `.pop()`; risco de `clear()` acidental
- [ ] **H6.T6** Seção: CORS e múltiplas interfaces — configuração para servir REST API, HTMX e Streamlit na mesma aplicação
- [ ] **H6.T7** Seção: structured logging por request — injeção de `request_id` e contexto de usuário em cada log entry

---

## Ordem de execução sugerida

| Prioridade | História | Justificativa |
|---|---|---|
| 1 | H1 — Testes | Está 90% pronto no `manifesto.md`; só falta transformar em cookbook com snippets |
| 2 | H2 — Reflexion Agent | Padrão mais central do projeto; base para entender H3, H5 e H6 |
| 3 | H4 — Hybrid Retrieval | Independente; relativamente autocontido |
| 4 | H3 — CRAG | Depende de entender H4 (retrieval) |
| 5 | H5 — Dual Memory | Depende de entender H2 (agent) e H3 (RAG) |
| 6 | H6 — FastAPI + LangGraph | Transversal; melhor escrever depois de H2–H5 |
