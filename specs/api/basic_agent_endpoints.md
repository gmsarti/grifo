# Especificação: Basic Agent Endpoints (API)

Este documento detalha os endpoints da API para interação com o **Reflexion Agent** e o **Vector Store**. O objetivo é prover uma interface robusta para um chat com LLM capaz de conversação e ingestão de documentos.

---

## 1. Chat & Agente (Reflexion Agent)

Este endpoint interage com o `AgentOrchestrator`, que encapsula o grafo de reflexão (LangGraph).

### POST `/api/v1/chat`
Envia uma mensagem para o agente.

**Request Body (JSON):**
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `message` | `string` | A mensagem ou pergunta do usuário. |
| `thread_id` | `string` | (Opcional) ID para rastrear a sessão e manter histórico. |
| `user_id` | `string` | (Opcional) ID para identificar o usuário. |

```json
{
  "message": "Como o design thinking pode ser aplicado na arquitetura?",
  "thread_id": "session-unique-id",
  "user_id": "user-1"
}
```

**Response Body (JSON):**
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `response` | `string` | Resposta final refinada pelo agente. |
| `thread_id` | `string` | ID da sessão utilizado. |
| `iterations` | `int` | Número de ciclos de reflexão realizados (máx: 2). |
| `references` | `list[string]` | Lista de fontes (URLs ou nomes de arquivos) consultadas no Vector Store. |
| `metadata` | `object` | Informações extras (latência, tokens consumidos). |

```json
{
  "response": "O design thinking na arquitetura permite focar no usuário através de etapas como...",
  "thread_id": "session-unique-id",
  "iterations": 2,
  "references": ["normas_abnt.pdf", "https://archdaily.com/artigo-1"],
  "metadata": {
    "latency_ms": 4500,
    "total_tokens": 1200
  }
}
```

---

## 2. Ingestão de Documentos (Vector Store)

Conjunto de endpoints para alimentar a base de conhecimento do agente.

### POST `/api/v1/ingest/upload`

Processa e armazena arquivos locais.

**Request (Multipart Form-Data):**

- `files`: Arquivos (suporte a `.pdf`, `.docx`, `.txt`, `.csv`).
- `collection_name`: (Opcional) Nome da coleção no ChromaDB (padrão: `default`).

**Response Body (JSON):**
```json
{
  "status": "success",
  "message": "2 arquivos processados com sucesso.",
  "processed_files": [
    { "filename": "especificacoes.pdf", "doc_id": "uuid-001" },
    { "filename": "contato.txt", "doc_id": "uuid-002" }
  ]
}
```

### POST `/api/v1/ingest/url`
Extrai e armazena conteúdo de uma página web.

**Request Body (JSON):**

```json
{
  "url": "https://developer.mozilla.org/pt-BR/docs/Web/HTML",
  "collection_name": "tech-docs"
}
```

**Response Body (JSON):**
```json
{
  "status": "success",
  "doc_id": "uuid-web-001",
  "metadata": {
    "title": "HTML: Linguagem de Marcação de Hipertexto | MDN",
    "chunks_created": 15
  }
}
```

---

## 3. Gerenciamento de Documentos & Memória

### GET `/api/v1/documents`
Lista todos os documentos presentes no Vector Store.

**Response Body (JSON):**
```json
{
  "documents": [
    { "doc_id": "uuid-001", "name": "especificacoes.pdf", "type": "file", "created_at": "2024-03-09T12:00:00Z" },
    { "doc_id": "uuid-web-001", "name": "MDN HTML", "type": "url", "created_at": "2024-03-09T14:30:00Z" }
  ]
}
```

### DELETE `/api/v1/documents/{doc_id}`
Remove permanentemente um documento e seus vetores.

---

## 4. Tratamento de Erros (Padrão)

Todas as falhas devem retornar um código de status HTTP apropriado e um detalhamento no corpo.

```json
{
  "error": {
    "code": "VECTOR_STORE_ERROR",
    "message": "Falha ao conectar ao banco de dados ChromaDB.",
    "details": "Connection timeout after 30s."
  }
}
```

---

## Estrutura de Injeção de Dependências

A implementação deve seguir os princípios de desacoplamento definidos:

- O **AgentOrchestrator** (classe de serviço) é injetado via `Depends` nos endpoints de chat.
- O **VectorStoreManager** (classe de serviço) é injetado nos endpoints de ingestão e listagem.

---

## Lista de Tasks (Backlog)

### 1. Chat & Agente
- [ ] [TASK-API-1] Implementar endpoint `POST /api/v1/chat` integrado ao `AgentOrchestrator`.
- [ ] [TASK-API-2] Adicionar suporte a `thread_id` para persistência de memória no chat.
- [ ] [TASK-API-3] Retornar referências (fontes) e metadados de execução no JSON de resposta.

### 2. Ingestão de Documentos
- [ ] [TASK-API-4] Implementar `POST /api/v1/ingest/upload` com suporte a multipart form-data.
- [ ] [TASK-API-5] Implementar `POST /api/v1/ingest/url` para processamento de links web.
- [ ] [TASK-API-6] Validar extensões de arquivo e tratar erros de parsing nos loaders.

### 3. Gerenciamento de Documentos
- [ ] [TASK-API-7] Implementar `GET /api/v1/documents` consumindo o `VectorStoreManager`.
- [ ] [TASK-API-8] Implementar `DELETE /api/v1/documents/{doc_id}` para remoção no ChromaDB e BM25.

### 4. Qualidade e Testes
- [ ] [TASK-API-9] Criar suíte de testes de integração para os endpoints de ingestão.
- [ ] [TASK-API-10] Validar o tratamento de erros padronizado em todos os endpoints.
