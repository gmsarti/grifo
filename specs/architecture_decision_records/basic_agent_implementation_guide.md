# Guia de Implementação: Basic Agent Stack

Este guia detalha os passos para implementar o Agent Stack, integrando o **Reflexion Agent**, o **Vector Store** e os **Endpoints de API**. Siga esta trilha para garantir que todas as camadas estejam alinhadas com as especificações técnicas.

---

## 1. Camada Utils (Ferramentas e Helpers)

*Focada em funções puras e processamento de dados base.*

- **Processamento de Texto:** Configurar o `RecursiveCharacterTextSplitter` com `chunk_size` e `chunk_overlap` ajustados para preservar o contexto semântico.
- **Geração de IDs (Upsert):** Implementar geração de IDs baseada em hashing do conteúdo do chunk para evitar duplicidade e suportar atualizações (Upsert) no banco vetorial.
- **Extração de Metadados:** Implementar rotinas para extrair automaticamente metadados padrão como fonte (URL ou arquivo), data, tipo e autor.

## 2. Camada Data Source (Acesso a Dados e Armazenamento)
*Integração com bases de dados e carregamento de documentos.*

- **ChromaDB:** Configurar a persistência local e inicialização da coleção de vetores.
- **BM25 Persistence:** Implementar a persistência em disco do índice BM25 para garantir busca híbrida consistente após reinicializações.
- **Document Loaders:**
  - `PyPDFLoader` (PDF), `Docx2txtLoader` (DOCX), `TextLoader` (TXT/CSV).
  - `WebBaseLoader` para URLs externas.
  - `GoogleDriveLoader` para integração com o Drive.

## 3. Camada API Clients (Integrações Externas)
*Clientes para serviços de terceiros.*

- **OpenAI:** Configurar instâncias para Embeddings e Chat, incluindo políticas de **retry** e **batching** para lidar com Rate Limits.
- **TavilySearch:** Configurar o cliente para ser utilizado como fallback dinâmico (CRAG) quando o contexto local for insuficiente.

## 4. Camada Processing (Regras de Negócio e Orquestração)
*O núcleo cognitivo da aplicação.*

### VectorStoreManager (RAG Motor)
- **Busca Híbrida:** Configurar o `EnsembleRetriever` combinando busca vetorial (Chroma) e por palavra-chave (BM25).
- **Reranking:** Implementar um Cross-Encoder (Document Compressor) para reordenar os resultados recuperados.
- **Retrieval Grader (CRAG):** Implementar a lógica de avaliação de relevância de documentos.
  - Se "Relevante": Segue para o agente.
  - Se "Irrelevante": Dispara busca web via TavilySearch e combina os resultados.

### AgentOrchestrator (Reflexion Agent)

- **Schemas Pydantic:** Implementar `Reflection`, `AnswerQuestion` e `ReviseAnswer`.
- **Grafo de Estados (LangGraph):**
  - **Draft Node:** Gera resposta inicial e primeira crítica (`Reflection`).
  - **Execute Tools:** Executa buscas via `VectorStoreManager` com base nas `search_queries`.
  - **Revise Node:** Revisa a resposta usando o feedback anterior e novos dados.
  - **MessagesState:** Manter o histórico completo para o revisor.
- **Loop de Controle:** Configurar o `event_loop` para o limite de `MAX_ITERATIONS = 2`.

## 5. Camada Presentation (Interface e API)
*Endpoints FastAPI e injeção de dependências.*

- **Endpoint Chat:** `POST /api/v1/chat`
  - Entrada: `message`, `thread_id`, `user_id`.
  - Injeta: `AgentOrchestrator`.
- **Endpoints de Ingestão:**
  - `POST /api/v1/ingest/upload`: Processamento de arquivos multipart form-data.
  - `POST /api/v1/ingest/url`: Processamento de conteúdo web (JSON).
  - Injeta: `VectorStoreManager`.
- **Endpoints de Gerenciamento:**
  - `GET /api/v1/documents`: Listagem de documentos.
  - `DELETE /api/v1/documents/{doc_id}`: Remoção física de vetores e metadados.

## 6. Qualidade, Testes e Observabilidade
*Garantia de maturidade do sistema.*

- **LangSmith Tracing:** Configurar rastreio de cada nó do agente e adicionar metadados como `iteration_count` e `total_tokens`.
- **Suite de Testes:**
  - Testes unitários para Loaders, Splitters e RetrievalGrader.
  - Testes de integração para o pipeline de busca (Ensemble -> Rerank -> Grader).
- **Evals (LLM-as-a-Judge):**
  - Dataset: `eval_dataset.json` e Golden Dataset (10 perguntas complexas).
  - Métricas: Hit Rate, Faithfulness e redução de superfluidades.