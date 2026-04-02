# Backlog Modular — Grifo

Bem-vindo ao novo sistema de backlog modular. Este arquivo serve como o **Quadro de Controle** central para o desenvolvimento do projeto.

## Estrutura do Backlog
Os detalhes técnicos das tarefas estão divididos por tema para facilitar a leitura e economizar tokens no contexto do LLM:

- [🛡️ Segurança](security.md): Autenticação, Rate Limiting, SAST, SCA, Secrets.
- [🐛 Bugs & Correções](bugs.md): Problemas de persistência, concorrência e lógica.
- [🚀 Funcionalidades & Melhorias](features.md): RAG, Multimodal, Streaming, Paginação.
- [🏗️ Plataforma & Infra](platform.md): Observabilidade, Evals, Docker, Typing.

---

## Quadro de Resumo e Status

| Status | ID | Título | Tipo | Prioridade | Detalhes |
|:---:|:---:|:---|:---:|:---:|:---|
| ✅ | B-001 | `SECRET_KEY` com valor padrão inseguro | Segurança | **Crítica** | [security.md](security.md#b-001-secret_key-com-valor-padrão-inseguro) |
| ✅ | B-002 | Memória de longo prazo apagada a cada restart | Bug | **Alta** | [bugs.md](bugs.md#b-002-memória-de-longo-prazo-apagada-a-cada-restart) |
| ✅ | B-003 | Índice BM25 perdido no restart com fallback silencioso | Bug | **Alta** | [bugs.md](bugs.md#b-003-índice-bm25-perdido-no-restart-com-fallback-silencioso) |
| ✅ | B-004 | `add_message` síncrono bloqueia o event loop | Bug | **Alta** | [bugs.md](bugs.md#b-004-add_message-síncrono-bloqueia-o-event-loop) |
| ✅ | B-005 | Cost tracking zerado ao usar Deepseek | Bug | **Alta** | [bugs.md](bugs.md#b-005-cost-tracking-zerado-ao-usar-deepseek) |
| ✅ | B-006 | Rate limiting ausente no endpoint de chat | Segurança | Média | [security.md](security.md#b-006-rate-limiting-ausente-no-endpoint-de-chat) |
| ✅ | B-007 | Sem limite de tamanho de arquivo na ingestão | Bug | Média | [bugs.md](bugs.md#b-007-sem-limite-de-tamanho-de-arquivo-na-ingestão) |
| ✅ | B-008 | Contagem de iterações da reflexão pode ser imprecisa | Bug | Média | [bugs.md](bugs.md#b-008-contagem-de-iterações-da-reflexão-pode-ser-imprecisa) |
| ✅ | B-009 | `AgenticRAGController` potencialmente recriado por request | Melhoria | Média | [features.md](features.md#b-009-agenticragcontroller-potencialmente-recriado-por-request) |
| ✅ | B-010 | Validação e sanitização do `system_prompt` | Segurança | Média | [security.md](security.md#b-010-validação-e-sanitização-do-system_prompt) |
| ❌ | B-011 | Streaming de resposta no endpoint de chat | Feature | Baixa | [features.md](features.md#b-011-streaming-de-resposta-no-endpoint-de-chat) |
| ❌ | B-012 | Paginação nos endpoints de listagem | Melhoria | Baixa | [features.md](features.md#b-012-paginação-nos-endpoints-de-listagem) |
| ✅ | B-013 | Pool de conexões ChromaDB | Melhoria | Baixa | [features.md](features.md#b-013-pool-de-conexões-chromadb) |
| ❌ | B-014 | Testes de integração dependentes de APIs externas | Melhoria | Baixa | [features.md](features.md#b-014-testes-de-integração-dependentes-de-apis-externas) |
| ❌ | B-015 | Chat multimodal — envio de imagens na conversa | Feature | Média | [features.md](features.md#b-015-chat-multimodal-envio-de-imagens-na-conversa) |
| ❌ | B-016 | Ingestão de imagens no knowledge base | Feature | Média | [features.md](features.md#b-016-ingestão-de-imagens-no-knowledge-base) |
| ✅ | B-017 | Verificação de Vulnerabilidades no Código (SAST) | Segurança | Média | [security.md](security.md#b-017-verificação-de-vulnerabilidades-no-código-sast) |
| ✅ | B-018 | Auditoria de Dependências (SCA) | Segurança | Média | [security.md](security.md#b-018-auditoria-de-dependências-sca) |
| ✅ | B-019 | Prevenção de Vazamento de Credenciais | Segurança | **Alta** | [security.md](security.md#b-019-prevenção-de-vazamento-de-credenciais) |
| ✅ | B-020 | Pipeline de Segurança Contínua (GitHub Actions) | Segurança | Média | [security.md](security.md#b-020-pipeline-de-segurança-contínua-github-actions) |
| ❌ | B-021 | Observabilidade e Tracing (LangSmith / Langfuse) | Plataforma | **Alta** | [platform.md](platform.md#b-021-observabilidade-e-tracing-langsmith-langfuse) |
| ❌ | B-022 | Pipeline de Avaliação de RAG (Evals) | Qualidade | Média | [platform.md](platform.md#b-022-pipeline-de-avaliação-de-rag-evals) |
| ❌ | B-023 | Containerização e Orquestração (Docker) | Infra | **Alta** | [platform.md](platform.md#b-023-containerização-e-orquestração-docker) |
| ❌ | B-024 | Checagem de Tipos Estática (Mypy) | Qualidade | Baixa | [platform.md](platform.md#b-024-checagem-de-tipos-estática-mypy) |
| ❌ | B-025 | Migrações de Banco de Dados (Alembic) | Infra | Média | [platform.md](platform.md#b-025-migrações-de-banco-de-dados-alembic) |
| ✅ | B-026 | Documentação de Arquitetura (Mermaid) | Doc | Baixa | [platform.md](platform.md#b-026-documentação-de-arquitetura-mermaid) |
| ✅ | B-027 | `VectorStoreManager` não é thread-safe | Bug | **Alta** | [bugs.md](bugs.md#b-027-vectorstoremanager-não-é-thread-safe) |
| ✅ | B-028 | BM25 desatualizado após exclusão de documento | Bug | Média | [bugs.md](bugs.md#b-028-bm25-fica-desatualizado-após-exclusão-de-documento) |
| ✅ | B-029 | `search_history` síncrono bloqueia o event loop | Bug | **Alta** | [bugs.md](bugs.md#b-029-search_history-síncrono-bloqueia-o-event-loop) |
| ❌ | B-030 | Embeddings acoplados ao provider OpenAI | Melhoria | Média | [features.md](features.md#b-030-embeddings-acoplados-ao-provider-openai) |
| ❌ | B-031 | `extract_knowledge` executa em toda interação | Melhoria | Baixa | [features.md](features.md#b-031-extract_knowledge-executa-em-toda-interação-sem-critério-de-relevância) |
| ❌ | B-032 | Checkpointer SQLite acumula dados indefinidamente | Bug | Média | [platform.md](platform.md#b-032-checkpointer-sqlite-acumula-dados-indefinidamente) |
| ❌ | B-033 | Banco de dados SQLite não suporta escalabilidade horizontal | Melhoria | Média | [platform.md](platform.md#b-033-banco-de-dados-sqlite-não-suporta-escalabilidade-horizontal) |

---

## Ordem de Execução Sugerida

### Fase 1 — Corretude (bugs que afetam resultados hoje)
1. **[B-027] Thread-safety do VectorStoreManager** (Bug/Alta) — Race condition silenciosa que corrompe o BM25 sob carga concorrente.
2. **[B-029] `search_history` síncrono** (Bug/Alta) — Bloqueia o event loop a cada consulta de memória; par do B-004 já corrigido.
3. **[B-028] BM25 desatualizado no delete** (Bug/Média) — Documentos deletados continuam aparecendo em buscas híbridas.
4. **[B-013] Pool de conexões ChromaDB** (Melhoria/Baixa) — Elimina recriação de instâncias Chroma por request; pré-requisito natural do B-027.

### Fase 2 — Segurança imediata
5. **[B-019] Prevenção de Vazamento de Credenciais** (Segurança/Alta) — Proteger chaves de API antes de qualquer exposição pública.
6. **[B-017] SAST & [B-018] SCA** (Segurança/Média) — Verificação estática do código e auditoria de dependências localmente.
7. **[B-020] Pipeline GitHub Actions** (CI/CD/Média) — Automatizar as verificações dos passos anteriores em cada PR.

### Fase 3 — Fundação de infra
8. **[B-023] Containerização (Docker)** (Infra/Alta) — Padronizar o ambiente; pré-requisito para B-033 (PostgreSQL).
9. **[B-025] Migrações de Banco (Alembic)** (Infra/Média) — Controle de schema antes de evoluir o modelo de dados.
10. **[B-032] GC do Checkpointer** (Bug/Média) — Impedir crescimento ilimitado do `grifo_memory.db`.
11. **[B-033] Migração para PostgreSQL** (Infra/Média) — Habilita múltiplos workers e deploy horizontal; depende de B-023 e B-025.

### Fase 4 — Observabilidade e qualidade
12. **[B-021] Observabilidade (LangSmith/Langfuse)** (Plataforma/Alta) — Fundamental para debugar o agente sobre a base estável das fases anteriores.
13. **[B-030] Embeddings desacoplados** (Melhoria/Média) — Prerequisito para trocar provider ou reduzir custos de embedding.
14. **[B-022] Avaliação de RAG (Evals)** (Qualidade/Média) — Criar baseline de métricas antes de otimizar prompts ou modelos.
15. **[B-024] Mypy** (Qualidade/Baixa) — Checagem estática de tipos para prevenir regressões.

### Fase 5 — Otimizações e features
16. **[B-031] `extract_knowledge` condicional** (Melhoria/Baixa) — Reduz custo por mensagem; só faz sentido após observabilidade medir o impacto real.
17. **[B-011] Streaming de resposta** (Feature/Baixa) — UX de resposta incremental.
18. **[B-015] Chat Multimodal** / **[B-016] Ingestão de imagens** — Novas capacidades sobre base sólida.
19. **[B-012] Paginação** / **[B-014] Testes mockados** — Polimento de API e CI.
