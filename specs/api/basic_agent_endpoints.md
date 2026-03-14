# Especificação: Basic Agent Endpoints (API)

Este documento detalha os endpoints da API para interação com o **Reflexion Agent** e o **Vector Store**. O objetivo é prover uma interface robusta para um chat com LLM capaz de conversação e ingestão de documentos.

---

## 1. Chat & Agente (Reflexion Agent)

Este endpoint interage com o `AgentOrchestrator`, que encapsula o grafo de reflexão (LangGraph).

### POST `/api/v1/chat`
Envia uma mensagem para o agente. Suporta o fluxo de reflexão e busca híbrida (CRAG). O fluxo é orquestrado dentro do contexto de um **Projeto** e **Thread**.

**Request Body (JSON):**
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `message` | `string` | A mensagem ou pergunta do usuário. |
| `project_id` | `string` | **Obrigatório**. ID do projeto atual. Isola a base de conhecimento. |
| `thread_id` | `string` | **Obrigatório**. ID da sessão (conversa) dentro do projeto. |
| `user_id` | `string` | (Opcional) ID para identificar o usuário. |
| `config` | `object` | (Opcional) Configurações da chamada (mode: "fast"|"reflexion", max_iterations, web_search). |

```json
{
  "message": "Como o design thinking pode ser aplicado na arquitetura?",
  "project_id": "my-architecture-project",
  "thread_id": "session-unique-id",
  "user_id": "user-1",
  "config": {
    "mode": "reflexion",
    "web_search": true
  }
}
```

**Response Body (JSON):**
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `response` | `string` | Resposta final refinada pelo agente. |
| `project_id` | `string` | ID do projeto utilizado. |
| `thread_id` | `string` | ID da sessão utilizado. |
| `iterations` | `int` | Número de ciclos de reflexão realizados. |
| `grounding_metadata` | `object` | Detalhes das fontes (local_docs vs web_search). |
| `process_trace` | `list` | Nós visitados no grafo. |
| `usage` | `object` | Consumo de tokens e latência. |

```json
{
  "response": "O design thinking na arquitetura permite focar no usuário através de etapas como...",
  "project_id": "my-architecture-project",
  "thread_id": "session-unique-id",
  "iterations": 2,
  "grounding_metadata": {
    "local_sources": ["normas_abnt.pdf"],
    "web_sources": ["https://archdaily.com/artigo-1"],
    "search_queries": ["design thinking architecture case studies"]
  },
  "process_trace": ["draft_node", "execute_tools", "revise_node"],
  "usage": {
    "latency_ms": 4500,
    "total_tokens": 1200,
    "estimated_cost_usd": 0.005
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
- `project_id`: **Obrigatório**. ID do projeto onde os documentos serão armazenados.
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
  "project_id": "my-architecture-project",
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
Lista todos os documentos presentes no Vector Store. Pode ser filtrado por projeto.

**Query Parameters:**
- `project_id`: (Opcional) Filtrar documentos por projeto.

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

### GET `/api/v1/memory/{thread_id}/facts`
Recupera fatos extraídos e armazenados na memória de longo prazo para uma thread.

**Response Body (JSON):**
```json
{
  "thread_id": "session-unique-id",
  "facts": [
    { "fact": "Usuário prefere respostas em Pt-BR técnico.", "confidence": 0.95 },
    { "fact": "Interesse em arquitetura sustentável.", "confidence": 0.88 }
  ]
}
```

### DELETE `/api/v1/memory/{thread_id}`
Limpa o histórico e os fatos associados a uma thread.

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
- [x] [TASK-API-1] Implementar endpoint `POST /api/v1/chat` integrado ao `AgentOrchestrator`.
- [x] [TASK-API-2] Adicionar suporte a `thread_id` e `config` no chat.
- [x] [TASK-API-3] Retornar `grounding_metadata` e `usage` no JSON de resposta.

### 2. Ingestão de Documentos
- [x] [TASK-API-4] Implementar `POST /api/v1/ingest/upload` com suporte a multipart form-data.
- [x] [TASK-API-5] Implementar `POST /api/v1/ingest/url` para processamento de links web.
- [x] [TASK-API-6] Validar extensões de arquivo e tratar erros de parsing nos loaders.

### 3. Gerenciamento de Documentos & Memória
- [x] [TASK-API-7] Implementar `GET /api/v1/documents` consumindo o `VectorStoreManager`.
- [x] [TASK-API-8] Implementar `DELETE /api/v1/documents/{doc_id}`.
- [x] [TASK-API-9] Implementar endpoints de memória (`/memory/{thread_id}`).

### 4. Qualidade e Testes
- [x] [TASK-API-10] Criar suíte de testes de integração para os endpoints de ingestão.
- [ ] [TASK-API-11] Validar o tratamento de erros padronizado em todos os endpoints.

### 5. Evolução e Aprendizado Contínuo
- [ ] [TASK-LEARN-1] Criar chain de extração de fatos (Knowledge Extraction) a partir do histórico.
- [ ] [TASK-LEARN-2] Implementar nó `summarize_memory` no LangGraph para rodar pós-interação.
- [ ] [TASK-LEARN-3] Implementar lógica de desduplicação e atualização de fatos existentes no Store.
- [ ] [TASK-LEARN-4] Validar persistência de longo prazo entre múltiplas threads do mesmo usuário.
