# Backlog — Funcionalidades & Melhorias

Este arquivo contém o detalhamento técnico de todas as novas funcionalidades e melhorias de arquitetura propostas.

---

### ✅ [B-009] `AgenticRAGController` potencialmente recriado por request

- **Tipo**: Melhoria
- **Prioridade**: Média
- **Área**: `app/services/`, `app/adapters/api/`

**Problema:**
Se o `AgenticRAGController` for instanciado dentro de uma função de dependência do FastAPI sem escopo de aplicação, o grafo RAG é recriado a cada request.

**Solução proposta:**
Garantir que `AgenticRAGController` e `AgentOrchestrator` sejam singletons usando o `lifespan` do FastAPI.

**Arquivos afetados:**
- `app/main.py`
- `app/adapters/api/` (injeção de dependência)

**Critério de aceite:**
- Uma única instância do agente e do controlador é criada por ciclo de vida da aplicação.

---

### ❌ [B-011] Streaming de resposta no endpoint de chat

- **Tipo**: Feature
- **Prioridade**: Baixa
- **Área**: `app/adapters/api/`, `frontend/`

**Problema:**
No modo de reflexão, uma resposta pode levar 20–60 segundos. O usuário fica sem feedback intermediário.

**Solução proposta:**
Usar `StreamingResponse` do FastAPI com `.astream_events()` do LangGraph para enviar tokens incrementalmente via SSE.

**Arquivos afetados:**
- `app/adapters/api/`
- `frontend/pages/2_Chat.py`

**Critério de aceite:**
- Tokens aparecem progressivamente na interface.

---

### ❌ [B-012] Paginação nos endpoints de listagem

- **Tipo**: Melhoria
- **Prioridade**: Baixa
- **Área**: `app/adapters/api/`

**Problema:**
`GET /api/projects` e `GET /api/v1/documents` retornam todos os itens sem limite.

**Solução proposta:**
Adicionar parâmetros `limit` e `offset` nos endpoints e nas queries.

**Arquivos afetados:**
- `app/adapters/api/`

**Critério de aceite:**
- Endpoints aceitam `limit` e `offset`.

---

### ❌ [B-013] Pool de conexões ChromaDB

- **Tipo**: Melhoria
- **Prioridade**: Baixa
- **Área**: `app/data_source/`, `app/processing/`

**Problema:**
`VectorStoreManager` e `VectorizedMessageHistory` criam uma nova instância `Chroma(...)` a cada chamada, gerando contenção de lock.

**Solução proposta:**
Centralizar o acesso ao ChromaDB num factory/cache que retorna instâncias já criadas.

**Arquivos afetados:**
- `app/data_source/vector_store.py`
- `app/processing/memory.py`

**Critério de aceite:**
- A mesma coleção retorna a mesma instância `Chroma`.

---

### ❌ [B-014] Testes de integração dependentes de APIs externas

- **Tipo**: Melhoria
- **Prioridade**: Baixa
- **Área**: `tests/`

**Problema:**
Testes de integração requerem chaves de API reais (OpenAI, Tavily), o que é custoso e instável para o CI.

**Solução proposta:**
Separar testes `live` com markers e usar mocks ou VCR cassetes para o CI.

**Arquivos afetados:**
- `tests/`
- `pyproject.toml`

**Critério de aceite:**
- Testes principais passam sem credenciais externas.

---

### ❌ [B-015] Chat multimodal — envio de imagens na conversa

- **Tipo**: Feature
- **Prioridade**: Média
- **Área**: `app/adapters/api/`, `app/schemas/`, `app/processing/`

**Problema:**
O endpoint de chat aceita apenas texto. Não há como enviar imagens para o agente analisar.

**Solução proposta:**
Estender o endpoint para aceitar `multipart/form-data` com um campo opcional `image`. O backend converte para base64 e monta a `HumanMessage` com conteúdo misto.

**Arquivos afetados:**
- `app/adapters/api/routers/chat.py`
- `app/processing/agent.py`

**Critério de aceite:**
- O agente responde sobre o conteúdo visual de imagens enviadas.

---

### ❌ [B-030] Embeddings acoplados ao provider OpenAI

- **Tipo**: Melhoria / Refactor
- **Prioridade**: Média
- **Área**: `app/data_source/`, `app/processing/`

**Problema:**
`OpenAIEmbeddings` está instanciado diretamente em dois lugares independentes:
- `app/data_source/vector_store.py` (`VectorStoreManager`)
- `app/processing/memory.py` (`VectorizedMessageHistory`)

O projeto já suporta DeepSeek como provider de LLM (via `settings.MODEL_PROVIDER`), mas os embeddings continuam acoplados à OpenAI. Trocar para `text-embedding-3-small`, usar embeddings locais (Ollama, FastEmbed) ou reduzir custos exige mudanças cirúrgicas em dois arquivos, com risco de inconsistência entre os índices de documentos e histórico.

**Solução proposta:**
Centralizar a criação do modelo de embeddings em `app/core/llm.py`:

```python
# app/core/llm.py
def get_embeddings():
    provider = settings.EMBEDDING_PROVIDER  # nova config, default "openai"
    if provider == "openai":
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,  # default "text-embedding-3-small"
            api_key=settings.OPENAI_API_KEY,
        )
    # futuramente: "ollama", "fastembed", etc.
    raise ValueError(f"Unsupported embedding provider: {provider}")
```

Substituir os dois `OpenAIEmbeddings(...)` por `get_embeddings()`.

**Arquivos afetados:**
- `app/core/llm.py`
- `app/core/config.py` (novas vars: `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`)
- `app/data_source/vector_store.py`
- `app/processing/memory.py`

**Critério de aceite:**
- Trocar `EMBEDDING_PROVIDER` no `.env` altera o modelo usado em ambos os componentes.
- `.env.example` documenta as novas variáveis.

---

### ❌ [B-031] `extract_knowledge` executa em toda interação sem critério de relevância

- **Tipo**: Melhoria
- **Prioridade**: Baixa
- **Área**: `app/processing/`

**Problema:**
`extract_knowledge_node` é o nó final obrigatório do grafo Reflexion — executa uma chamada adicional ao LLM **em toda mensagem**, mesmo para perguntas triviais ("qual é a capital do Brasil?", "obrigado"). Isso adiciona latência e custo de tokens sem produzir nenhum fato relevante na maioria dos casos.

**Solução proposta:**
Tornar `extract_knowledge_node` condicional: só executá-lo quando o `revisor` sinalizar que a interação contém informação nova. Uma abordagem limpa é adicionar um campo ao `ReflexionState`:

```python
class ReflexionState(MessagesState):
    iteration_count: Annotated[int, operator.add]
    has_new_knowledge: bool  # sinalizado pelo revise_node
```

O `revise_node` pode setar `has_new_knowledge=True` apenas quando a resposta revisada contiver fatos do usuário (ex: identificou preferências, nome, contexto de trabalho). O `event_loop` então roteia para `extract_knowledge` ou `END` dependendo do flag.

**Arquivos afetados:**
- `app/processing/agent.py`

**Critério de aceite:**
- Perguntas sem conteúdo pessoal/factual não disparam chamada de extração.
- Logs mostram claramente quando a extração é pulada vs executada.

---

### ❌ [B-016] Ingestão de imagens no knowledge base

- **Tipo**: Feature
- **Prioridade**: Média
- **Área**: `app/data_source/`

**Problema:**
A ingestão aceita apenas documentos de texto/PDF. Não há pipeline para extrair significado de imagens para o RAG.

**Solução proposta:**
Adicionar um `ImageIngestionLoader` que usa um modelo de visão para descrever a imagem e indexá-la como texto no ChromaDB.

**Arquivos afetados:**
- `app/data_source/loaders.py`

**Critério de aceite:**
- Imagens são indexadas e tornam-se pesquisáveis via RAG.
