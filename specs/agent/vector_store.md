# Especificação: Vector Store (RAG)

Este documento define a arquitetura, funcionalidades e o plano de implementação para o módulo de armazenamento e busca vetorial (Vector Store) do **Projeto Grifo**.

## Arquitetura e Tecnologias

- **Banco de Dados Vetorial:** [ChromaDB](https://www.trychroma.com/)
- **Framework de Orquestração:** [LangChain](https://www.langchain.com/)
- **Embeddings:** `OpenAIEmbeddings` (via OpenAI API)
- **Text Splitting:** `RecursiveCharacterTextSplitter`
- **Retrieval:** Busca Híbrida combinando Busca Vetorial (Chroma) e BM25.
- **Reranking:** Uso de Cross-Encoder (ex: Cohere ou BGE Reranker) para refinamento de resultados.
- **Extração de Metadados:** Processamento prévio para extração de autor, data, fonte e categoria.
- **Retrieval Grader (CRAG):** Uso de LLM estruturado para avaliar a relevância dos documentos recuperados.
- **Web Search Fallback:** Integração com TavilySearch para busca externa quando o contexto local é insuficiente.

## Requisitos Funcionais

### 1. Ingestão de Dados

O sistema deve ser capaz de processar e ingerir diferentes fontes de informação:

- **Arquivos Locais:** Suporte a múltiplos formatos (PDF, TXT, CSV, DOCX).
- **URLs:** Ingestão de conteúdo web através do `WebBaseLoader`.
- **Google Drive:** Integração via `GoogleDriveLoader`.
- **Processamento:**
  - Uso de `RecursiveCharacterTextSplitter` para fragmentação inteligente.
  - **Extração de Metadados:** Identificação automática de metadados (Data de criação, Autor, Fonte, Tipo de documento, Categoria) para permitir Self-Querying.
  - **Gerenciamento de Estado:** Suporte a Upsert (baseado em hashing de conteúdo) e rotinas de exclusão.
  - **Rate Limit Handling:** Implementação de políticas de retry e batching para chamadas de API (OpenAI).

### 2. Recuperação (Retrieval Avançado)

A busca de contexto deve ser robusta:

- **Busca Vetorial:** Recuperação por similaridade semântica utilizando ChromaDB.
- **BM25:** Recuperação baseada em palavras-chave com persistência do índice em disco.
- **Filtros de Metadados:** Suporte a pré-filtros (ex: buscar apenas em PDFs de uma data específica).
- **Busca Híbrida + Rerank:**
  1. Recuperação inicial via Ensemble (Vector + BM25).
  2. Re-pontuação (Reranking) dos candidatos via Cross-Encoder.
- **Retrieval Grading & Web Fallback (Corrective RAG):**
  - O `VectorStoreManager.search` executa a busca híbrida.
  - O `retrieval_grader` avalia os documentos.
  - **Fluxo de Decisão:**
    - Se "Relevante": Retorna documentos para o agente.
    - Se "Irrelevante/Ambíguo": Dispara busca via TavilySearch, combina resultados e retorna o contexto aumentado.
  - Isso garante que o agente receba sempre a melhor informação sem precisar gerenciar múltiplos fluxos de busca web.

### 3. Observabilidade e Qualidade

- **Rastreabilidade:** Integração com LangSmith ou Langfuse para monitorar a qualidade dos chunks recuperados.
- **Testes:** Testes unitários para splitters/loaders e testes de integração para o fluxo de RAG.

---

## Lista de Tasks (Backlog)

### Ingestão & Gerenciamento de Dados

- [ ] [TASK-1] Configurar `RecursiveCharacterTextSplitter` com parâmetros ideais (chunk_size, chunk_overlap).
- [ ] [TASK-2] Implementar `FileIngestionService` para suportar diferentes extensões de arquivo.
- [ ] [TASK-3] Implementar `WebIngestionService` utilizando `WebBaseLoader`.
- [ ] [TASK-4] Implementar `GoogleDriveIngestionService` utilizando `GoogleDriveLoader`.
- [ ] [TASK-5] Integrar ingestores com a persistência do ChromaDB.
- [ ] [TASK-12] Implementar estratégia de geração de IDs únicos (hashing) para suporte a operações de Upsert.
- [ ] [TASK-13] Criar rotinas de exclusão e atualização de documentos no ChromaDB e no índice BM25.
- [ ] [TASK-14] Implementar extração de metadados padrão (fonte, data, tipo) nos serviços de ingestão.
- [ ] [TASK-15] Configurar política de retry e batching no cliente da OpenAI (Rate Limit Handling).

### Recuperação (Retrieval Avançado)

- [ ] [TASK-6] Configurar `BM25Retriever` a partir dos documentos ingeridos.
- [ ] [TASK-7] Configurar `EnsembleRetriever` para combinar Busca Vetorial e BM25.
- [ ] [TASK-8] Expor interface de busca simplificada no `VectorStoreManager`.
- [ ] [TASK-16] Implementar sistema de persistência em disco para o estado/índice do BM25Retriever.
- [ ] [TASK-17] Adicionar componente de Document Compressor / Reranker após o EnsembleRetriever para refinar os resultados.
- [ ] [TASK-18] Implementar suporte a pré-filtros de busca (Metadata Filtering) no VectorStoreManager.
- [ ] [TASK-19] Implementar `RetrievalGrader` (Structured Output) para validar relevância de documentos.
- [ ] [TASK-20] Integrar lógica de Corrective RAG (CRAG) para lidar com documentos irrelevantes.

### Qualidade e Testes

#### Testes Unitários

- [ ] [TASK-9.1] Validar loaders (PDF, URL, Google Drive) com mocks para garantir extração correta de texto.
- [ ] [TASK-9.2] Testar `RecursiveCharacterTextSplitter` (overlap e chunk size) em diferentes volumes de texto.
- [ ] [TASK-9.3] Validar a extração de metadados (autor, data, fonte) para cada tipo de loader.
- [ ] [TASK-9.4] Testar o `RetrievalGrader` com prompts controlados e outputs estruturados.

#### Testes de Integração

- [ ] [TASK-10.1] Pipeline de Ingestão: Testar fluxo completo do arquivo até a persistência no Chroma e BM25.
- [ ] [TASK-10.2] Pipeline de Busca: Validar fluxo Ensemble -> Rerank -> Grader -> Contexto Final.
- [ ] [TASK-10.3] Testar resiliência a Rate Limits da OpenAI com retries e logs de erro.

#### Avaliação de Recuperação (RAG Evaluation)

- [ ] [TASK-21] Criar um `eval_dataset.json` com pares de Pergunta/Contexto esperado.
- [ ] [TASK-22] Implementar métricas de Hit Rate e Faithfulness usando ferramentas de eval (ex: RAGAS ou similar).
- [ ] [TASK-23] Configurar rastreamento de custos e latência via LangSmith.

#### Documentação

- [ ] [TASK-11] Criar exemplos práticos de uso do `VectorStoreManager` no `README.md`.
- [ ] [TASK-24] Documentar o esquema de metadados para facilitar consultas por outros componentes.
