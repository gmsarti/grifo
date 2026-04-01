# Backlog — Bugs & Correções

Este arquivo contém o detalhamento técnico de todos os bugs identificados e as correções propostas.

---

### ✅ [B-002] Memória de longo prazo apagada a cada restart

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/processing/`

**Problema:**
`AgentOrchestrator` usa `InMemoryStore()` por padrão. Todo restart do servidor apaga todos os fatos aprendidos pelo agente. O README documenta isso como "persiste entre sessões", o que é falso.

**Solução proposta:**
Substituir `InMemoryStore` por um store persistente. O LangGraph oferece integrações oficiais:
- **Opção A (mais simples):** `langgraph-checkpoint-sqlite` — persiste em um arquivo SQLite, sem nova dependência de infraestrutura.

**Arquivos afetados:**
- `app/processing/agent.py`
- `app/core/config.py` (nova var `MEMORY_STORE_URL`)

**Critério de aceite:**
- Fatos salvos numa sessão persistem após restart do servidor
- README atualizado para refletir o comportamento real

---

### ✅ [B-003] Índice BM25 perdido no restart com fallback silencioso

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/data_source/`

**Problema:**
O `VectorStoreManager` mantém `self.bm25_retriever` e `self._all_documents` apenas em memória. Após um restart, ambos são `None`/`[]`. O método `search_hybrid` detecta isso mas cai silenciosamente para busca vetorial pura.

**Solução proposta:**
1. **Reconstruir o BM25 na inicialização** lendo os documentos já existentes no ChromaDB.
2. **Logar quando o fallback ocorre** para que o comportamento seja observável.

**Arquivos afetados:**
- `app/data_source/vector_store.py`

**Critério de aceite:**
- Após restart, uma busca híbrida usa BM25 corretamente.
- O fallback para busca vetorial gera um log de warning.

---

### ✅ [B-004] `add_message` síncrono bloqueia o event loop

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/processing/`

**Problema:**
`VectorizedMessageHistory.add_message` chama `self.vector_store.add_texts()`, que é síncrono e bloqueia o event loop enquanto escreve no disco.

**Solução proposta:**
Executar a operação síncrona em um thread pool:

```python
import asyncio
loop = asyncio.get_event_loop()
await loop.run_in_executor(None, self.vector_store.add_texts, ...)
```

**Arquivos afetados:**
- `app/processing/memory.py`

**Critério de aceite:**
- Operações de escrita na memória de curto prazo não bloqueiam o event loop.

---

### ✅ [B-005] Cost tracking zerado ao usar Deepseek

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/processing/`

**Problema:**
O `AgentOrchestrator` usa `get_openai_callback()` para rastrear tokens e custo. Quando `MODEL_PROVIDER=deepseek`, os campos retornam zero.

**Solução proposta:**
Extrair tokens diretamente da resposta do LangChain via `response.usage_metadata`, que é agnóstico ao provider.

**Arquivos afetados:**
- `app/processing/agent.py`

**Critério de aceite:**
- Com `MODEL_PROVIDER=deepseek`, os tokens são rastreados corretamente.

---

### ✅ [B-007] Sem limite de tamanho de arquivo na ingestão

- **Tipo**: Bug / Melhoria
- **Prioridade**: Média
- **Área**: `app/data_source/`

**Problema:**
`FileIngestionService` não tem limite de tamanho máximo para arquivos. Arquivos gigantes podem consumir toda a RAM e gerar custos elevados.

**Solução proposta:**
Adicionar validação de tamanho com limite configurável (ex: 50MB).

**Arquivos afetados:**
- `app/data_source/loaders.py`
- `app/core/config.py`

**Critério de aceite:**
- Upload de arquivo acima do limite retorna erro claro.

---

### ✅ [B-027] `VectorStoreManager` não é thread-safe

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/data_source/`

**Problema:**
`VectorStoreManager` mantém `self._all_documents` (lista mutável) e reconstrói `self.bm25_retriever` in-place em `add_documents()`. Com múltiplos workers do Uvicorn ou requisições de ingestão concorrentes, duas chamadas simultâneas a `add_documents()` podem corromper silenciosamente a lista `_all_documents` e o índice BM25 em memória. O bug não lança exceção — o retriever simplesmente retorna resultados errados.

**Solução proposta:**
Proteger as operações de mutação com um `asyncio.Lock` por instância:

```python
import asyncio

class VectorStoreManager:
    def __init__(self, project_id: str = "default"):
        ...
        self._lock = asyncio.Lock()

    async def add_documents(self, documents: list[Document]):
        async with self._lock:
            self._all_documents.extend(documents)
            await asyncio.get_event_loop().run_in_executor(
                None, self.vector_store.add_documents, documents
            )
            self._rebuild_bm25()
```

**Arquivos afetados:**
- `app/data_source/vector_store.py`

**Critério de aceite:**
- Ingestões concorrentes não corrompem `_all_documents` nem o índice BM25.
- Testes de concorrência com `asyncio.gather` em múltiplas ingestões passam sem race condition.

---

### ✅ [B-028] BM25 fica desatualizado após exclusão de documento

- **Tipo**: Bug
- **Prioridade**: Média
- **Área**: `app/data_source/`

**Problema:**
`delete_document()` remove o documento do ChromaDB e de `_all_documents`, mas **não reconstrói** o índice BM25. Um comentário no próprio código reconhece isso:
```python
# Por simplicidade, assumimos que o BM25 será recriado na próxima adição
```
Isso significa que buscas BM25/híbridas podem continuar retornando chunks de documentos já deletados até que uma nova ingestão ocorra.

**Solução proposta:**
Reconstruir o BM25 e o HybridRetriever imediatamente após a remoção, se ainda houver documentos:

```python
def delete_document(self, doc_id: str):
    self.vector_store.delete(where={"source": doc_id})
    self._all_documents = [
        d for d in self._all_documents if d.metadata.get("source") != doc_id
    ]
    if self._all_documents:
        self._rebuild_bm25()
    else:
        self.bm25_retriever = None
        self.hybrid_retriever = None
```

Extrair a lógica de rebuild para um método privado `_rebuild_bm25()` reutilizável.

**Arquivos afetados:**
- `app/data_source/vector_store.py`

**Critério de aceite:**
- Após `delete_document()`, busca híbrida não retorna chunks do documento deletado.
- Teste unitário cobre o cenário de delete seguido de search.

---

### ✅ [B-029] `search_history` síncrono bloqueia o event loop

- **Tipo**: Bug
- **Prioridade**: Alta
- **Área**: `app/processing/`

**Problema:**
`VectorizedMessageHistory.search_history()` chama `self.vector_store.similarity_search()`, que é **síncrono** e realiza I/O de disco (leitura do ChromaDB). Ele é chamado dentro de `retrieve_memory_node`, que é um nó `async` do LangGraph. Isso bloqueia o event loop durante a busca — o mesmo problema que B-004 corrigiu para `add_message`, mas que permanece no `search_history`.

**Solução proposta:**
Executar a busca síncrona em um thread pool executor:

```python
import asyncio

async def search_history_async(self, query: str, k: int = 3) -> str:
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None, self.vector_store.similarity_search, query, k
    )
    ...
```

Alternativamente, verificar se a versão da `langchain-chroma` usada oferece `asimilarity_search()` e substituir diretamente.

**Arquivos afetados:**
- `app/processing/memory.py`
- `app/processing/agent.py` (atualizar chamada)

**Critério de aceite:**
- `retrieve_memory_node` não bloqueia o event loop durante busca no ChromaDB.
- Teste de carga confirma que outras corrotinas progridem durante a busca.

---

### ✅ [B-008] Contagem de iterações da reflexão pode ser imprecisa

- **Tipo**: Bug
- **Prioridade**: Média
- **Área**: `app/processing/`

**Problema:**
`event_loop` conta tool calls numa janela fixa dos últimos 10 mensagens, o que pode falhar se houver muitas mensagens de contexto.

**Solução proposta:**
Usar um contador explícito no estado do LangGraph (`iteration_count`).

**Arquivos afetados:**
- `app/processing/agent.py`

**Critério de aceite:**
- O agente respeita `MAX_ITERATIONS` independentemente do volume de mensagens de contexto.
