<p align="center">
  <img src="img/grifo_carcara_no_bg.png" alt="Grifo Mascote" width="200">
</p>

# Grifo

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12">
  <img src="https://img.shields.io/badge/LangChain-latest-green.svg" alt="LangChain">
  <img src="https://img.shields.io/badge/Streamlit-1.55-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/ChromaDB-latest-orange.svg" alt="ChromaDB">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT">
</p>

> [!IMPORTANT]
> **Status: Em desenvolvimento.**
> As funcionalidades planejadas e as especificações detalhadas podem ser encontradas na pasta `specs/`

Este repositório é uma implementação padrão de referência para aplicações de Agentes de IA baseada no padrão de **3 camadas (3-Tier Architecture)**. O objetivo é fornecer uma estrutura robusta, escalável e pronta para a era dos Agentes de IA (2024-2026).

## 🚀 Funcionalidades Principais

- 🧠 **Agente Reflexivo**: Orquestração de raciocínio avançado com ciclos de crítica e refinamento.
- 📚 **RAG (Retrieval-Augmented Generation)**: Busca semântica eficiente utilizando ChromaDB.
- 🛠️ **Ecossistema de Ferramentas**: Integração nativa com ferramentas e APIs externas.
- 🖥️ **Interface Reativa (HTMX)**: Experiência SPA moderna com FastAPI + HTMX + Tailwind CSS.
- 🏗️ **Arquitetura Clean/Hexagonal**: Desacoplamento estrito entre lógica de negócio, persistência e interfaces.

## 🏗️ Arquitetura do Sistema

O projeto segue princípios de **Clean Architecture**, dividindo o sistema em camadas concêntricas que protegem o domínio.

```mermaid
graph TD
    User((Usuário))

    subgraph "Adapters (Interfaces)"
        Web[app/web/ - HTMX/HTML]
        API[app/api/ - REST JSON]
    end

    subgraph "Application Layer"
        Services[app/services/ - Lógica de Negócio]
        RAGFacade[app/services/rag_service_facade.py]
    end

    subgraph "Domain & Persistence"
        Repos[app/repositories/ - Repository Pattern]
        Models[app/models/ - SQLAlchemy]
        Schemas[app/schemas/ - Pydantic]
    end

    subgraph "Core AI Engine"
        IA[app/processing/ - LangGraph/RAG]
    end

    User --> Web
    User --> API
    Web --> Services
    API --> Services
    Services --> Repos
    Services --> RAGFacade
    Repos --> Models
    RAGFacade --> IA
```

---

## 📂 Estrutura do Projeto

- **[app/core/](file:///home/gusarti/pessoal/code/agent-stack/app/core/)**: Configurações globais, segurança e dependências infra.
- **[app/api/](file:///home/gusarti/pessoal/code/agent-stack/app/api/)**: Adaptadores REST que servem contratos em JSON.
- **[app/web/](file:///home/gusarti/pessoal/code/agent-stack/app/web/)**: Adaptadores UI que servem fragmentos HTML para o HTMX.
- **[app/services/](file:///home/gusarti/pessoal/code/agent-stack/app/services/)**: Orquestradores da lógica de negócio e Fachada de IA.
- **[app/repositories/](file:///home/gusarti/pessoal/code/agent-stack/app/repositories/)**: Abstração da persistência (SQLAlchemy).
- **[app/models/](file:///home/gusarti/pessoal/code/agent-stack/app/models/)**: Definições das entidades do banco de dados.
- **[app/schemas/](file:///home/gusarti/pessoal/code/agent-stack/app/schemas/)**: Contratos de dados (Pydantic).
- **[app/processing/](file:///home/gusarti/pessoal/code/agent-stack/app/processing/)**: O motor de IA, LangGraph e definições do Agente.
- **[app/data_source/](file:///home/gusarti/pessoal/code/agent-stack/app/data_source/)**: Mecânica de RAG (loaders e vector_store).

## 🛠️ Como Rodar

### Pré-requisitos
- Python 3.12+
- Gerenciador de dependências [uv](https://github.com/astral-sh/uv) (recomendado) ou `pip`.

### Instalação

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/projeto-grifo.git
   cd projeto-grifo
   ```

2. **Configure o ambiente:**

   ```bash
   # Usando uv (recomendado)
   uv venv
   source .venv/bin/activate  # Linux/macOS
   uv sync
   ```

3. **Configuração de Variáveis:**

   Crie um arquivo `.env` na raiz do projeto seguindo o modelo e adicione suas chaves de API:
   ```env
   OPENAI_API_KEY=sua_chave_aqui
   ```

4. **Execute a aplicação:**

   ```bash
   streamlit run app/presentation/web_ui.py
   ```

---

## 📜 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 👤 Autor

**Gustavo** - *AI Enthusiast & Developer*
- LinkedIn: [@gmsarti](https://www.linkedin.com/in/gmsarti/)
- GitHub: [@gmsarti](https://github.com/gmsarti)