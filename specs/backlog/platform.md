# Backlog — Plataforma & Infraestrutura

Este arquivo contém as tarefas para elevar o projeto ao padrão ouro de engenharia (Observabilidade, Evals, CI/CD e Infra).

---

### ❌ [B-021] Observabilidade e Tracing (LangSmith / Langfuse)

- **Tipo**: Melhoria / Plataforma
- **Prioridade**: Alta
- **Área**: Observabilidade

**Problema:**
Atualmente, debugar o fluxo do LangGraph depende de logs JSON no console. É difícil visualizar a árvore de chamadas, os custos por nó e identificar o ponto exato de falha ou latência em cadeias complexas.

**Solução proposta:**
Integrar uma ferramenta de tracing especializada em LLMs.
1. Adicionar suporte a `LANGCHAIN_TRACING_V2` (LangSmith) ou `langfuse`.
2. Configurar o cliente de tracing no `AgentOrchestrator`.
3. Adicionar as chaves necessárias ao `.env.example`.

**Arquivos afetados:**
- `app/core/config.py`
- `app/processing/agent.py`
- `.env.example`

**Critério de aceite:**
- Cada conversa gera um rastro completo (trace) visível na dashboard da ferramenta escolhida.
- Metadados como `user_id` e `project_id` são propagados para o rastro.

---

### ❌ [B-022] Pipeline de Avaliação de RAG (Evals)

- **Tipo**: Melhoria / Qualidade
- **Prioridade**: Média
- **Área**: IA / Testes

**Problema:**
Não há uma forma quantitativa de medir a qualidade das respostas do RAG. Mudanças no prompt ou no modelo de embedding podem degradar a performance sem que a equipe perceba.

**Solução proposta:**
Implementar um framework de avaliação (ex: **Ragas** ou **Deepeval**).
1. Criar um conjunto de dados "padrão ouro" (Ground Truth).
2. Criar um script de teste que mede *Faithfulness* (fidelidade ao contexto) e *Answer Relevancy*.
3. Integrar no pipeline de desenvolvimento.

**Arquivos afetados:**
- `tests/integration/test_evals.py` (novo)
- `pyproject.toml` (novas dependências: `ragas` ou `deepeval`)

**Critério de aceite:**
- Execução de um comando simples que reporta o score técnico da qualidade do RAG.

---

### ❌ [B-023] Containerização e Orquestração (Docker)

- **Tipo**: Infraestrutura
- **Prioridade**: Alta
- **Área**: DevOps

**Problema:**
O projeto depende de setup local (Python 3.12, SQLite, ChromaDB local). Isso dificulta o onboarding de novos devs e o deploy em servidores de produção.

**Solução proposta:**
Criar arquivos de containerização profissional.
1. `Dockerfile`: Multi-stage build otimizado para Python.
2. `docker-compose.yml`: Orquestrar o Backend, Frontend e o serviço do ChromaDB.

**Arquivos afetados:**
- `Dockerfile` (novo)
- `docker-compose.yml` (novo)
- `.dockerignore` (novo)

**Critério de aceite:**
- `docker-compose up` sobe todo o ecossistema funcional sem necessidade de venv local.

---

### ❌ [B-024] Checagem de Tipos Estática (Mypy)

- **Tipo**: Qualidade / Segurança
- **Prioridade**: Baixa
- **Área**: Desenvolvimento

**Problema:**
O projeto usa type hints, mas não há validação estática no CI. Erros de tipo (NoneType, Incompatible types) só são pegos em runtime.

**Solução proposta:**
Configurar o **Mypy** para garantir a integridade dos dados entre os serviços.
1. Adicionar `mypy` como dependência de dev.
2. Configurar o `tool.mypy` no `pyproject.toml`.
3. Adicionar hook no `pre-commit`.

**Arquivos afetados:**
- `pyproject.toml`
- `.pre-commit-config.yaml`

**Critério de aceite:**
- `mypy .` roda sem erros ou com exceções explicitamente permitidas.

---

### ❌ [B-025] Migrações de Banco de Dados (Alembic)

- **Tipo**: Melhoria / Infraestrutura
- **Prioridade**: Média
- **Área**: Persistência

**Problema:**
A persistência em banco de dados é feita de forma direta. Se o esquema da tabela de sessões ou usuários mudar, não há um histórico de migrações controlado.

**Solução proposta:**
Integrar o **Alembic** para gerenciar mudanças no banco SQLite.
1. Inicializar diretório de migrações.
2. Configurar conexão com o banco de produção via `settings`.

**Arquivos afetados:**
- `alembic/` (novo)
- `alembic.ini` (novo)
- `app/core/db.py`

**Critério de aceite:**
- Mudanças nas models do banco podem ser aplicadas via `alembic upgrade head`.

---

### ❌ [B-032] Checkpointer SQLite acumula dados indefinidamente

- **Tipo**: Bug / Infra
- **Prioridade**: Média
- **Área**: `app/processing/`

**Problema:**
`AgentOrchestrator.process_message()` gera um `invocation_id = f"{thread_id}_{uuid4()}"` único por chamada para evitar que tool_calls de invocações anteriores poluam o estado do grafo. Isso é correto, mas tem um efeito colateral: o `AsyncSqliteSaver` (checkpointer) armazena o estado de cada invocação no `grifo_memory.db` e esse estado **nunca é lido novamente** nem deletado. O arquivo cresce sem limite proporcional ao uso do sistema.

**Solução proposta:**
Implementar uma rotina de limpeza (GC) dos checkpoints obsoletos:

1. Adicionar uma função `cleanup_old_checkpoints(max_age_hours: int)` que deleta entradas do SQLite com `thread_id` contendo o padrão `_{uuid}` e `created_at` mais antigos que o limite.
2. Agendar a rotina via `lifespan` do FastAPI (ex: a cada 24h com `asyncio.create_task`).

```python
async def cleanup_old_checkpoints(db_path: str, max_age_hours: int = 48):
    async with aiosqlite.connect(db_path) as db:
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        await db.execute(
            "DELETE FROM checkpoints WHERE thread_id LIKE '%_%' AND created_at < ?",
            (cutoff.isoformat(),)
        )
        await db.commit()
```

**Arquivos afetados:**
- `app/processing/agent.py`
- `app/main.py` (agendamento no lifespan)
- `app/core/config.py` (nova var: `CHECKPOINT_MAX_AGE_HOURS`, default 48)

**Critério de aceite:**
- `grifo_memory.db` não cresce além do esperado após uso contínuo.
- Limpeza é logada com contagem de registros removidos.

---

### ❌ [B-033] Banco de dados SQLite não suporta escalabilidade horizontal

- **Tipo**: Melhoria / Infra
- **Prioridade**: Média
- **Área**: Persistência

**Problema:**
O projeto usa SQLite para três finalidades distintas — banco relacional (`sql_app.db`), checkpointer do LangGraph e store de memória de longo prazo (ambos em `grifo_memory.db`). SQLite suporta apenas um writer concorrente. Com múltiplos workers Uvicorn (ex: `--workers 4`) ou múltiplos containers, todas as escritas disputam o mesmo arquivo e resultam em `database is locked`. Escalar horizontalmente não é possível sem trocar o backend.

**Solução proposta:**
Migrar para **PostgreSQL** como banco relacional e de estado:

1. Substituir `aiosqlite` por `asyncpg` no SQLAlchemy (`postgresql+asyncpg://`).
2. Usar `langgraph-checkpoint-postgres` para o checkpointer (suporte oficial do LangGraph).
3. Usar `langgraph-store-postgres` ou tabela própria para o store de memória.
4. Manter SQLite como opção de desenvolvimento local via `DATABASE_URL` no `.env`.

**Dependência:** B-023 (Docker) e B-025 (Alembic) devem ser concluídos antes — o Docker orquestrará o PostgreSQL e o Alembic gerenciará as migrações.

**Arquivos afetados:**
- `app/core/db.py`
- `app/processing/agent.py`
- `app/core/config.py`
- `pyproject.toml` (novas deps: `asyncpg`, `langgraph-checkpoint-postgres`)
- `docker-compose.yml` (serviço PostgreSQL)

**Critério de aceite:**
- Aplicação funciona com `DATABASE_URL=postgresql+asyncpg://...` em produção.
- SQLite continua funcional como default para desenvolvimento local.
- `docker-compose up` sobe PostgreSQL automaticamente.

---

### ✅ [B-026] Documentação de Arquitetura (Mermaid)

- **Tipo**: Melhoria / Documentação
- **Prioridade**: Baixa
- **Área**: Documentação

**Problema:**
A arquitetura de 3 camadas e o grafo do LangGraph estão detalhados apenas em código, dificultando o entendimento por novos colaboradores.

**Solução proposta:**
Criar diagramas dinâmicos usando Mermaid.js.
1. Documentar o fluxo do `AgenticRAGController`.
2. Documentar o modelo de dados e a arquitetura das 3 camadas (Flow, Service, Adapter).

**Arquivos afetados:**
- `docs/architecture.md` (novo)

**Critério de aceite:**
- Diagramas renderizáveis no GitHub/VSCode documentando os fluxos principais.
