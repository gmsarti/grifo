# Implementation Plan - Clean Architecture API & Web

Este plano detalha a transição da Prova de Conceito para uma infraestrutura blindada, utilizando o padrão **Repository** e separação total entre **Web (HTMX)** e **API (REST)**.

## Estrutura de Pastas Final (Hexagonal/Clean)

```text
app/
├── api/                 # Port: REST JSON Adapters
│   └── routers/           # auth.py, projects.py, chat.py
├── web/                 # Port: UI/HTMX Adapters
│   ├── routes/
│   ├── templates/       # Jinja2
│   └── static/
├── core/                # Infrastructure: Security, Config, DI
├── models/              # Persistence: SQLAlchemy Entities
├── repositories/        # Persistence: Data Access Logic (Desacoplamento)
├── services/            # Business Logic / Orchestration
├── schemas/             # Data Contracts: Pydantic
└── processing/          # AI Engine: LangGraph/RAG (Círculo Interno)
```

---

## Implementation Backlog

### [PHASE 0] Infraestrutura e Repositórios (Blindagem)
- [x] **[TASK-0.1] Setup de Pastas**: Criar a nova hierarquia e organizar arquivos atuais.
- [x] **[TASK-0.2] Base de Dados e Base Repository**:
    - Configurar `app/core/db.py` (Async).
    - Criar `app/repositories/base_repository.py` com métodos genéricos.
- [x] **[TASK-0.3] Migrações**: Configurar Alembic para suportar a nova estrutura de `app/models/`. (Nota: Tabelas criadas via Base.metadata em testes)

### [PHASE 1] Domínio de Autenticação (Épico 1)
- [x] **[TASK-1.1] Persistence**: Criar `app/models/user.py` e `app/repositories/user_repository.py`.
- [x] **[TASK-1.2] Security**: Hashing de senhas e JWT em `app/core/security.py`. (Implementado em `app/services/auth_service.py` e `app/api/deps.py`)
- [x] **[TASK-1.3] Service**: `app/services/auth_service.py` (Orquestra repositório e segurança).

### [PHASE 2] Gestão de Projetos (Épico 2)
- [x] **[TASK-2.1] Repository**: CRUD de Projetos isolado em `app/repositories/project_repository.py`.
- [x] **[TASK-2.2] Service**: Lógica de "Workspace Padrão" no `app/services/project_service.py`.
- [x] **[TASK-2.3] Adapters**: Rotas REST em `app/api/routers/projects.py`.

### [PHASE 3] Engine de Chat e RAG Facade (Épicos 3 e 4)
- [ ] **[TASK-3.1] RAG Facade**: 
    - [NEW] [rag_service.py](file:///home/gusarti/pessoal/code/agent-stack/app/services/rag_service.py): Encapsular `AgenticRAGController` e lidar com persistência de mensagens.
- [ ] **[TASK-3.2] Persistência de Mensagens**:
    - [NEW] [chat.py](file:///home/gusarti/pessoal/code/agent-stack/app/models/chat.py): Modelos `Session` e `Message`.
    - [NEW] [chat_repository.py](file:///home/gusarti/pessoal/code/agent-stack/app/repositories/chat_repository.py): CRUD de sessões e histórico.
- [ ] **[TASK-3.3] Adapters Web**: Primeiras rotas HTMX em `app/web/routes/chat.py`.

### [PHASE 4] Ingestão e UI (Épicos 5 e 6)
- [ ] **[TASK-4.1] Document Service**: Gestão de upload e vetores.
- [ ] **[TASK-4.2] UI Dashboard**: Construção do template base e parcials para o chat reativo.

---

## Estratégia de Verificação
*   **Unit Tests de Serviço**: Testar lógica de negócio mockando os Repositórios.
*   **Integration Tests**: Validar o fluxo RAG Service -> Repositório -> Banco.
