# Grifo — Documentação de Arquitetura

Este documento descreve a arquitetura do Grifo com diagramas gerados via Mermaid.js, renderizáveis no GitHub e no VSCode (extensão Markdown Preview Mermaid Support).

---

## 1. Visão Geral — Arquitetura em 3 Camadas

O Grifo segue um padrão de 3 camadas: **Adapter** (apresentação), **Service** (lógica de negócio) e **Processing/Data** (agente e persistência).

```mermaid
graph TD
    subgraph ADAPTER["Adapter Layer — Apresentação"]
        A1["FastAPI Router\n/auth, /projects, /v1"]
        A2["chat_endpoint()"]
        A3["Auth / Deps\nOAuth2 + JWT"]
        A4["Web UI\nJinja2 + Static"]
    end

    subgraph SERVICE["Service Layer — Negócio"]
        S1["AgentOrchestrator\nReflexion Graph"]
        S2["AgenticRAGController\nCRAG Graph"]
        S3["ProjectService"]
        S4["AuthService"]
        S5["RAGService"]
    end

    subgraph PROCESSING["Processing Layer — Agente & RAG"]
        P1["LangGraph\nReflexion StateGraph"]
        P2["LangGraph\nCAG StateGraph"]
        P3["Chains\nfirst_responder / revisor\nextract_knowledge"]
        P4["Memory\nVectorizedMessageHistory\nStoreMemoryManager"]
    end

    subgraph DATA["Data Layer — Persistência"]
        D1["SQLite (Async)\nUsers, Projects\nSessions, Messages"]
        D2["ChromaDB\nVector Store\n+ BM25 Hybrid"]
        D3["AsyncSqliteStore\nLong-term Facts"]
        D4["AsyncSqliteSaver\nGraph Checkpoints"]
    end

    subgraph EXTERNAL["Serviços Externos"]
        E1["LLM Providers\nOpenAI / DeepSeek"]
        E2["Tavily\nWeb Search"]
        E3["LangSmith\nTracing (Opcional)"]
    end

    A2 --> S1
    A1 --> S3
    A1 --> S4
    S1 --> P1
    S1 --> S2
    S2 --> P2
    P1 --> P3
    P1 --> P4
    P2 --> D2
    P4 --> D2
    P4 --> D3
    P1 --> D4
    S3 --> D1
    S4 --> D1
    S5 --> D1
    P3 --> E1
    P2 --> E1
    P2 --> E2
    P1 --> E3
```

---

## 2. Fluxo de uma Requisição de Chat

```mermaid
sequenceDiagram
    actor User
    participant API as chat_endpoint()
    participant Orch as AgentOrchestrator
    participant Graph as Reflexion Graph
    participant RAG as AgenticRAGController
    participant Mem as Memory (Short + Long)
    participant LLM as LLM Provider

    User->>API: POST /v1/chat {message, thread_id, project_id}
    API->>Orch: process_message(message, thread_id, project_id)
    Orch->>Graph: ainvoke(messages, config)

    Graph->>Mem: retrieve_memory_node()
    Mem-->>Graph: contexto (histórico vetorial + fatos)

    Graph->>LLM: draft_node() — fast_llm
    LLM-->>Graph: AnswerQuestion (draft + reflection + queries)

    Graph->>RAG: execute_tools → get_company_knowledge()
    RAG-->>Graph: documentos recuperados

    Graph->>LLM: revise_node() — reasoner_llm
    LLM-->>Graph: ReviseAnswer (resposta revisada)

    alt iteration_count < MAX_ITERATIONS
        Graph->>Graph: event_loop() → volta ao execute_tools
    else Iterações concluídas
        Graph->>LLM: extract_knowledge_node()
        LLM-->>Graph: fatos extraídos
        Graph->>Mem: StoreMemoryManager.save_fact()
    end

    Graph-->>Orch: estado final com mensagens
    Orch-->>API: ChatResponse {response, usage, grounding_metadata}
    API-->>User: 200 OK
```

---

## 3. Grafo do Agente Reflexion (LangGraph)

```mermaid
stateDiagram-v2
    [*] --> retrieve_memory
    retrieve_memory --> draft

    draft --> execute_tools : AnswerQuestion tool call

    execute_tools --> revise

    revise --> event_loop : iteration_count++

    state event_loop <<choice>>
    event_loop --> execute_tools : iteration_count < MAX_ITERATIONS
    event_loop --> extract_knowledge : iteration_count >= MAX_ITERATIONS

    extract_knowledge --> [*]
```

**Nós do grafo:**

| Nó | Modelo | Responsabilidade |
|----|--------|-----------------|
| `retrieve_memory` | — | Busca histórico vetorizado + fatos de longo prazo |
| `draft` | `fast_llm` (gpt-4o-mini) | Gera resposta inicial com reflexão e queries de busca |
| `execute_tools` | ToolNode | Executa `AnswerQuestion` / `ReviseAnswer` |
| `revise` | `reasoner_llm` (gpt-4o) | Refina a resposta com base na reflexão |
| `extract_knowledge` | `reasoner_llm` | Extrai fatos novos e persiste na memória de longo prazo |

---

## 4. Grafo do CRAG — AgenticRAGController

```mermaid
flowchart TD
    START([Início]) --> retrieve

    retrieve["retrieve()\nHybrid Search\nvector + BM25 via RRF\nk=3 documentos"]

    retrieve --> grade_documents

    grade_documents["grade_documents()\nretrieval_grader chain\nclassifica relevância\nbinary: yes / no"]

    grade_documents --> decide{decide_to_generate}

    decide -- "web_search = true\nsem docs relevantes" --> web_search_node

    decide -- "web_search = false\ndocs relevantes encontrados" --> generate

    web_search_node["web_search()\nReescreve query\nTavilySearch max_results=3\nAnexo como Document"]

    web_search_node --> generate

    generate["generate()\nrag_generation_chain\nreasoner_llm\nSíntese final com contexto"]

    generate --> END([Fim])
```

**Estado do grafo (`GraphState`):**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `question` | `str` | Pergunta do usuário |
| `generation` | `str` | Resposta gerada |
| `web_search` | `bool` | Flag: fallback para busca web |
| `documents` | `list[Document]` | Documentos recuperados/filtrados |

---

## 5. Modelo de Dados (ER)

```mermaid
erDiagram
    User {
        int id PK
        string full_name
        string email UK
        string hashed_password
        bool is_active
        bool is_superuser
    }

    Project {
        int id PK
        string name
        text description
        text system_prompt
        int owner_id FK
        bool is_active
    }

    Session {
        int id PK
        int project_id FK
        datetime created_at
    }

    Message {
        int id PK
        int session_id FK
        string role
        text content
        datetime created_at
    }

    User ||--o{ Project : "possui"
    Project ||--o{ Session : "contém"
    Session ||--o{ Message : "contém"
```

---

## 6. Arquitetura de Memória

```mermaid
graph LR
    subgraph SHORT["Memória de Curto Prazo"]
        SM1["VectorizedMessageHistory\nChromaDB\ncollection: history_{project_id}_{thread_id}"]
    end

    subgraph LONG["Memória de Longo Prazo"]
        LM1["StoreMemoryManager\nAsyncSqliteStore\nnamespace: (memories, user_id)"]
    end

    subgraph STATE["Estado do Grafo"]
        GS1["AsyncSqliteSaver\nCheckpointer\ngrifo_memory.db"]
    end

    retrieve_memory -- "search_history(query)" --> SM1
    retrieve_memory -- "search_memories(user_id, query)" --> LM1
    extract_knowledge -- "save_fact(topic, fact)" --> LM1
    graph_execution -- "persiste estado" --> GS1
    SM1 -- "add_message()" --> new_messages
    GS1 -- "restaura estado" --> graph_execution
```

---

## 7. Pipeline de Ingestão de Documentos

```mermaid
flowchart TD
    A([Upload de Arquivo\n ou URL]) --> B{Tipo de fonte}

    B -- Arquivo -- > C["FileIngestionService\nValidação: extensão, tamanho max 50MB\nPDF, DOCX, CSV, TXT, MD"]
    B -- URL --> D["WebIngestionService\nWebBaseLoader(url)"]

    C --> E["RecursiveCharacterTextSplitter\nchunk_size=1000\noverlap=200"]
    D --> E

    E --> F["VectorStoreManager.add_documents()"]

    F --> G["ChromaDB\nVector Embeddings\nOpenAIEmbeddings"]
    F --> H["BM25 Index\nReconstruído sobre todos os docs"]

    G --> I["HybridRetriever\nRRF: score = 1/(60+rank_vec) + 1/(60+rank_bm25)"]
    H --> I

    I --> J[(Persistido em\n./data/chroma/{project_id})]
```

---

## 8. Componentes e Arquivos Principais

```mermaid
graph TD
    subgraph app
        main["main.py\nFastAPI + lifespan"]

        subgraph adapters
            api_main["adapters/api/main.py\nRouter principal"]
            chat_router["routers/chat.py\nchat_endpoint()"]
            auth_router["routers/auth.py"]
            proj_router["routers/projects.py"]
            deps["deps.py\nget_current_user()"]
        end

        subgraph core
            config["core/config.py\nSettings"]
            db["core/db.py\nAsyncSession"]
            llm_factory["core/llm.py\nget_reasoner()\nget_fast_model()"]
        end

        subgraph services
            orchestrator["processing/agent.py\nAgentOrchestrator"]
            rag_facade["services/rag_service_facade.py\nAgenticRAGController"]
            rag_service["services/rag_service.py\nRAGService"]
        end

        subgraph processing
            rag_graph["processing/rag/graph.py\ncreate_rag_graph()"]
            rag_nodes["processing/rag/nodes.py\nretrieve, grade,\ngenerate, web_search"]
            chains["processing/chains.py\nfirst_responder\nrevisor\nknowledge_extractor"]
            memory["processing/memory.py\nVectorizedMessageHistory\nStoreMemoryManager"]
        end

        subgraph data_source
            vector_store["data_source/vector_store.py\nVectorStoreManager"]
            loaders["data_source/loaders.py\nFileIngestionService\nWebIngestionService"]
        end

        subgraph models
            user_model["models/user.py — User"]
            proj_model["models/project.py — Project"]
            chat_models["models/chat.py — Session, Message"]
        end

        subgraph repositories
            user_repo["repositories/user.py"]
            proj_repo["repositories/project.py"]
            chat_repo["repositories/chat.py"]
        end
    end

    main --> adapters
    main --> core
    chat_router --> orchestrator
    orchestrator --> rag_graph
    orchestrator --> rag_facade
    rag_facade --> rag_graph
    rag_graph --> rag_nodes
    rag_nodes --> vector_store
    orchestrator --> chains
    orchestrator --> memory
    memory --> vector_store
    services --> repositories
    repositories --> db
```
