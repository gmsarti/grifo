# Backlog — Grifo

Baseado na avaliação técnica realizada em 2026-03-26.

Cada item segue o formato:

> **[ID] Título**
> - **Tipo**: Bug | Segurança | Melhoria | Feature
> - **Prioridade**: Crítica | Alta | Média | Baixa
> - **Área**: qual camada/módulo é afetado
> - **Problema**: o que está errado ou faltando hoje
> - **Solução proposta**: o que fazer
> - **Arquivos afetados**: lista de arquivos relevantes
> - **Critério de aceite**: como saber que está pronto

---

## Crítico

### ✅ [B-001] SECRET_KEY com valor padrão inseguro

- **Tipo**: Segurança
- **Prioridade**: Crítica
- **Área**: `app/core/`

**Problema:**
`config.py` define `SECRET_KEY: str = "supersecretkey"`. Se o arquivo `.env` não declarar essa variável, todos os JWTs são assinados com uma chave trivial e publicamente conhecida. Qualquer pessoa pode forjar tokens de autenticação válidos.

**Solução proposta:**
Remover o valor padrão, tornando a variável obrigatória. A aplicação deve recusar a iniciar se `SECRET_KEY` não estiver definida no ambiente — ou, como segunda opção, validar que o valor não é o padrão e lançar um erro na startup.

```python
# config.py
SECRET_KEY: str  # sem default — obriga definição no .env

# main.py (ou lifespan)
if settings.SECRET_KEY in ("supersecretkey", "", "changeme"):
    raise RuntimeError("SECRET_KEY insegura. Defina um valor forte no .env.")
```

**Arquivos afetados:**
- `app/core/config.py`
- `app/main.py` (validação na startup)
- `.env.example` (documentar que o valor é obrigatório)

**Critério de aceite:**
- A aplicação não inicia sem `SECRET_KEY` definida no `.env`
- Testes de startup validam o comportamento
- `.env.example` possui instrução clara sobre como gerar uma chave segura (`openssl rand -hex 32`)

---

## Alta Prioridade

### ✅ [B-002] Memória de longo prazo apagada a cada restart

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/processing/`

**Problema:**
`AgentOrchestrator` usa `InMemoryStore()` por padrão. Todo restart do servidor apaga todos os fatos aprendidos pelo agente. O README documenta isso como "persiste entre sessões", o que é falso.

**Solução proposta:**
Substituir `InMemoryStore` por um store persistente. O LangGraph oferece integrações oficiais:

- **Opção A (mais simples):** `langgraph-checkpoint-sqlite` — persiste em um arquivo SQLite, sem nova dependência de infraestrutura.
- **Opção B (produção):** `langgraph-checkpoint-postgres` com Redis ou PostgreSQL.

A escolha deve ser configurável via variável de ambiente para manter flexibilidade entre desenvolvimento e produção.

```python
# agent.py
from langgraph.store.sqlite import SqliteStore  # exemplo

store = SqliteStore("./data/memory_store.db")
self.store = store
```

**Arquivos afetados:**
- `app/processing/agent.py`
- `app/core/config.py` (nova var `MEMORY_STORE_URL`)
- `pyproject.toml` (nova dependência)

**Critério de aceite:**
- Fatos salvos numa sessão persistem após restart do servidor
- Testes de integração verificam persistência entre instâncias distintas do `AgentOrchestrator`
- README atualizado para refletir o comportamento real

---

### ✅ [B-003] Índice BM25 perdido no restart com fallback silencioso

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/data_source/`

**Problema:**
O `VectorStoreManager` mantém `self.bm25_retriever` e `self._all_documents` apenas em memória. Após um restart, ambos são `None`/`[]`. O método `search_hybrid` detecta isso mas cai silenciosamente para busca vetorial pura — sem log, sem aviso, sem exceção:

```python
def search_hybrid(self, query: str, k: int = 3) -> list[Document]:
    if not self.hybrid_retriever:
        return self.vector_store.similarity_search(query, k=k)  # fallback silencioso
```

O usuário acredita estar usando busca híbrida, mas não está.

**Solução proposta:**
Duas ações independentes:

1. **Reconstruir o BM25 na inicialização** lendo os documentos já existentes no ChromaDB:
```python
def _rebuild_bm25_from_chroma(self):
    result = self.vector_store.get(include=["documents", "metadatas"])
    if result["documents"]:
        docs = [Document(page_content=t, metadata=m)
                for t, m in zip(result["documents"], result["metadatas"])]
        self._all_documents = docs
        self.bm25_retriever = BM25Retriever.from_documents(docs, k=5)
        self.hybrid_retriever = HybridRetriever(...)
```

2. **Logar quando o fallback ocorre** para que o comportamento seja observável:
```python
if not self.hybrid_retriever:
    logger.warning("BM25 retriever not available, falling back to vector search only.")
    return self.vector_store.similarity_search(query, k=k)
```

**Arquivos afetados:**
- `app/data_source/vector_store.py`

**Critério de aceite:**
- Após restart, uma busca híbrida em um projeto com documentos já indexados usa BM25 corretamente
- O fallback para busca vetorial gera um log de warning quando ocorre
- Testes de integração verificam o comportamento pós-restart

---

### ✅ [B-004] `add_message` síncrono bloqueia o event loop

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/processing/`

**Problema:**
`VectorizedMessageHistory.add_message` é declarado `async`, mas internamente chama `self.vector_store.add_texts()`, que é síncrono e bloqueia o event loop enquanto escreve no disco. Com múltiplas requisições simultâneas, isso degrada a concorrência da API.

```python
async def add_message(self, message: BaseMessage):
    ...
    self.vector_store.add_texts(...)  # bloqueia o event loop
```

**Solução proposta:**
Executar a operação síncrona em um thread pool para não bloquear o loop:

```python
import asyncio

async def add_message(self, message: BaseMessage):
    ...
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None, self.vector_store.add_texts, [content], [metadata]
    )
```

Alternativamente, avaliar se a versão do `langchain-chroma` já oferece métodos `aadd_texts` ou `aadd_documents`.

**Arquivos afetados:**
- `app/processing/memory.py`

**Critério de aceite:**
- Operações de escrita na memória de curto prazo não bloqueiam o event loop
- Teste de concorrência passa: duas requisições simultâneas não se bloqueiam mutuamente

---

### ✅ [B-005] Cost tracking zerado ao usar Deepseek

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/processing/`

**Problema:**
O `AgentOrchestrator.process_message` usa `get_openai_callback()` para rastrear tokens e custo. Esse callback é específico do SDK da OpenAI. Quando `MODEL_PROVIDER=deepseek`, os campos `total_tokens` e `total_cost` retornam zero — o usuário não tem rastreamento de custo.

**Solução proposta:**
Tornar o tracking condicional ao provider, com um fallback neutro:

```python
from contextlib import nullcontext

def _get_cost_tracker(self):
    if settings.MODEL_PROVIDER == "openai":
        return get_openai_callback()
    return nullcontext()  # retorna objeto sem atributos de custo
```

Ou extrair tokens diretamente da resposta do LangChain via `response.usage_metadata`, que é agnóstico ao provider:

```python
usage = result["messages"][-1].usage_metadata  # tokens no objeto de resposta
```

**Arquivos afetados:**
- `app/processing/agent.py`

**Critério de aceite:**
- Com `MODEL_PROVIDER=deepseek`, os tokens são rastreados corretamente ou, se não disponíveis, o campo retorna `null` com um log de aviso — sem retornar zeros enganosos

---

## Média Prioridade

### ✅ [B-006] Rate limiting ausente no endpoint de chat

- **Tipo**: Segurança / Melhoria
- **Prioridade**: Média
- **Área**: `app/adapters/api/`

**Problema:**
`POST /api/v1/chat` chama LLMs caros (GPT-4o) sem nenhuma proteção contra abuso. Um único usuário autenticado pode disparar centenas de requisições e gerar custos inesperados.

**Solução proposta:**
Adicionar rate limiting por usuário usando `slowapi` (integração nativa com FastAPI):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat")
@limiter.limit("20/minute")
async def chat_endpoint(...):
    ...
```

Tornar os limites configuráveis via `.env` (`RATE_LIMIT_CHAT=20/minute`).

**Arquivos afetados:**
- `app/adapters/api/` (rotas de chat)
- `app/core/config.py`
- `pyproject.toml`

**Critério de aceite:**
- Requisições acima do limite retornam `429 Too Many Requests`
- Limite é configurável por variável de ambiente
- Testes verificam o comportamento de throttling

---

### ❌ [B-007] Sem limite de tamanho de arquivo na ingestão

- **Tipo**: Bug / Melhoria
- **Prioridade**: Média
- **Área**: `app/data_source/`

**Problema:**
`FileIngestionService.validate_file` verifica extensão e arquivo vazio, mas não tem limite de tamanho máximo. Um arquivo de 500MB seria aceito, consumindo toda a RAM disponível durante o processamento e gerando custo elevado de embeddings.

**Solução proposta:**
Adicionar validação de tamanho com limite configurável:

```python
MAX_FILE_SIZE_MB: int = 50  # em config.py

def validate_file(self, file_path: str):
    ...
    size_mb = stat.st_size / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise ValueError(
            f"Arquivo muito grande: {size_mb:.1f}MB. Limite: {settings.MAX_FILE_SIZE_MB}MB"
        )
```

**Arquivos afetados:**
- `app/data_source/loaders.py`
- `app/core/config.py`

**Critério de aceite:**
- Upload de arquivo acima do limite retorna erro claro com tamanho máximo informado
- Limite é configurável via `.env`

---

### ❌ [B-008] Contagem de iterações da reflexão pode ser imprecisa

- **Tipo**: Bug
- **Prioridade**: Média
- **Área**: `app/processing/`

**Problema:**
`event_loop` conta tool calls numa janela fixa dos últimos 10 mensagens. Quando há muitas `SystemMessages` de contexto de memória no início do estado, essa janela pode não capturar todas as iterações — o agente pode executar mais ciclos do que `MAX_ITERATIONS`.

```python
for msg in state["messages"][-10:]  # janela arbitrária
```

**Solução proposta:**
Contar todas as mensagens do estado atual em vez de uma janela arbitrária, ou usar um contador explícito no estado:

```python
# Opção A: contar em todo o estado
tool_calls_count = sum(
    1 for msg in state["messages"]
    if isinstance(msg, AIMessage) and msg.tool_calls
)

# Opção B: adicionar campo de contador ao estado
class ReflexionState(MessagesState):
    iteration_count: int
```

A Opção B é mais robusta e mais legível.

**Arquivos afetados:**
- `app/processing/agent.py`

**Critério de aceite:**
- Com `REFLEXION_MAX_ITERATIONS=2`, o agente executa exatamente 2 iterações independentemente do volume de mensagens de contexto no estado
- Testes parametrizados verificam o comportamento com 1, 2 e 3 iterações máximas

---

### 🔄 [B-009] `AgenticRAGController` potencialmente recriado por request

- **Tipo**: Melhoria
- **Prioridade**: Média
- **Área**: `app/services/`, `app/adapters/api/`

**Problema:**
Se `AgenticRAGController` for instanciado dentro de uma função de dependência do FastAPI sem escopo de aplicação (`app`), o grafo RAG é recriado a cada request — compilando o grafo LangGraph desnecessariamente.

**Solução proposta:**
Garantir que `AgenticRAGController` e `AgentOrchestrator` sejam singletons na vida da aplicação, usando o `lifespan` do FastAPI:

```python
# main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = AgentOrchestrator()
    app.state.rag_controller = AgenticRAGController()
    yield

app = FastAPI(lifespan=lifespan)
```

**Arquivos afetados:**
- `app/main.py`
- `app/adapters/api/` (injeção de dependência)
- `app/services/rag_service_facade.py`

**Critério de aceite:**
- Uma única instância do agente e do controlador RAG é criada por ciclo de vida da aplicação
- Teste verifica que a mesma instância é retornada em chamadas consecutivas

---

### ✅ [B-010] Validação e sanitização do `system_prompt`

- **Tipo**: Segurança
- **Prioridade**: Média
- **Área**: `app/schemas/`, `app/adapters/api/`

**Problema:**
Via API, um usuário pode definir um `system_prompt` com conteúdo arbitrariamente longo ou com tentativas de prompt injection para contornar o comportamento esperado do agente.

**Solução proposta:**
- Definir tamanho máximo para `system_prompt` (ex: 2000 caracteres) via validador Pydantic
- Documentar claramente que o campo é confiável apenas para usuários administradores do projeto

```python
from pydantic import field_validator

class ProjectCreate(BaseModel):
    system_prompt: str | None = None

    @field_validator("system_prompt")
    def validate_system_prompt(cls, v):
        if v and len(v) > 2000:
            raise ValueError("system_prompt não pode exceder 2000 caracteres")
        return v
```

**Arquivos afetados:**
- `app/schemas/project.py`

**Critério de aceite:**
- `system_prompt` acima do limite retorna `422 Unprocessable Entity`
- Testes cobrem casos de borda (None, vazio, no limite, acima do limite)

---

## Baixa Prioridade / Melhorias

### ❌ [B-011] Streaming de resposta no endpoint de chat

- **Tipo**: Feature
- **Prioridade**: Baixa
- **Área**: `app/adapters/api/`, `frontend/`

**Problema:**
Com `REFLEXION_MAX_ITERATIONS=2` e RAG incluído, uma resposta pode levar 20–60 segundos. O usuário fica com a tela parada sem nenhum feedback intermediário.

**Solução proposta:**
Usar `StreamingResponse` do FastAPI com o `.astream_events()` do LangGraph para enviar tokens incrementalmente via Server-Sent Events (SSE):

```python
from fastapi.responses import StreamingResponse

@router.post("/chat/stream")
async def chat_stream(...):
    async def event_generator():
        async for event in agent.graph.astream_events(inputs, config=config):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

Atualizar o frontend Streamlit para consumir o stream usando `requests` com `stream=True`.

**Arquivos afetados:**
- `app/adapters/api/` (novo endpoint ou parâmetro `stream=true`)
- `frontend/pages/2_Chat.py`

**Critério de aceite:**
- Tokens aparecem progressivamente na interface durante a geração
- O endpoint não-streaming continua funcionando (não quebra retro-compatibilidade)

---

### ❌ [B-012] Paginação nos endpoints de listagem

- **Tipo**: Melhoria
- **Prioridade**: Baixa
- **Área**: `app/adapters/api/`

**Problema:**
`GET /api/projects` e `GET /api/v1/documents` retornam todos os itens sem limite. Com crescimento do uso, a resposta pode se tornar impraticável.

**Solução proposta:**
Adicionar parâmetros `limit` e `offset` (ou `page` e `page_size`) nos endpoints e nas queries dos repositórios:

```python
@router.get("/projects")
async def list_projects(limit: int = 20, offset: int = 0, ...):
    return await project_service.list(limit=limit, offset=offset)
```

**Arquivos afetados:**
- `app/adapters/api/` (rotas de projetos e documentos)
- `app/repositories/project_repository.py`

**Critério de aceite:**
- Endpoints aceitam `limit` e `offset`
- Resposta inclui `total` para o cliente calcular páginas
- Testes verificam paginação com datasets de tamanhos variados

---

### ❌ [B-013] Pool de conexões ChromaDB

- **Tipo**: Melhoria
- **Prioridade**: Baixa
- **Área**: `app/data_source/`, `app/processing/`

**Problema:**
`VectorStoreManager` e `VectorizedMessageHistory` criam uma nova instância `Chroma(...)` a cada chamada. Com múltiplas requisições simultâneas, isso pode gerar contenção de lock no arquivo do ChromaDB.

**Solução proposta:**
Centralizar o acesso ao ChromaDB num factory/cache que retorna instâncias já criadas para o mesmo `collection_name`:

```python
_chroma_instances: dict[str, Chroma] = {}

def get_chroma_collection(collection_name: str, persist_dir: str) -> Chroma:
    if collection_name not in _chroma_instances:
        _chroma_instances[collection_name] = Chroma(
            collection_name=collection_name,
            persist_directory=persist_dir,
            embedding_function=get_embeddings(),
        )
    return _chroma_instances[collection_name]
```

**Arquivos afetados:**
- `app/data_source/vector_store.py`
- `app/processing/memory.py`

**Critério de aceite:**
- A mesma coleção retorna a mesma instância `Chroma` dentro do mesmo processo
- Teste de concorrência não gera erros de lock no ChromaDB

---

### ❌ [B-014] Testes de integração dependentes de APIs externas

- **Tipo**: Melhoria
- **Prioridade**: Baixa
- **Área**: `tests/`

**Problema:**
Parte dos testes de integração parece requerer chaves de API reais (OpenAI, Tavily). Isso torna o CI dependente de credenciais e gera custo a cada execução.

**Solução proposta:**
- Separar testes que requerem APIs reais com um marker `@pytest.mark.live` e excluí-los do CI por padrão
- Para o caminho principal do CI, usar mocks ou VCR cassetes (biblioteca `pytest-recording`) que gravam e reproduzem respostas HTTP

```bash
# CI: só roda testes sem dependência externa
uv run pytest -m "not live"

# Localmente, com APIs reais
uv run pytest -m live
```

**Arquivos afetados:**
- `tests/` (markers nos testes existentes)
- `pyproject.toml` (configuração dos markers)
- `.github/workflows/` (se existir CI)

**Critério de aceite:**
- `uv run pytest -m "not live"` passa sem nenhuma chave de API definida
- Documentação clara sobre como rodar os testes `live` localmente

---

## Resumo

| Status | ID | Título | Tipo | Prioridade |
|--------|-----|--------|------|------------|
| ✅ | B-001 | `SECRET_KEY` com valor padrão inseguro | Segurança | **Crítica** |
| ✅ | B-002 | Memória de longo prazo apagada a cada restart | Bug | **Alta** |
| ✅ | B-003 | Índice BM25 perdido no restart com fallback silencioso | Bug | **Alta** |
| ✅ | B-004 | `add_message` síncrono bloqueia o event loop | Bug | **Alta** |
| ✅ | B-005 | Cost tracking zerado ao usar Deepseek | Bug | **Alta** |
| ✅ | B-006 | Rate limiting ausente no endpoint de chat | Segurança | Média |
| ❌ | B-007 | Sem limite de tamanho de arquivo na ingestão | Bug | Média |
| ❌ | B-008 | Contagem de iterações da reflexão pode ser imprecisa | Bug | Média |
| 🔄 | B-009 | `AgenticRAGController` potencialmente recriado por request | Melhoria | Média |
| ✅ | B-010 | Validação e sanitização do `system_prompt` | Segurança | Média |
| ❌ | B-011 | Streaming de resposta no endpoint de chat | Feature | Baixa |
| ❌ | B-012 | Paginação nos endpoints de listagem | Melhoria | Baixa |
| ❌ | B-013 | Pool de conexões ChromaDB | Melhoria | Baixa |
| ❌ | B-014 | Testes de integração dependentes de APIs externas | Melhoria | Baixa |
