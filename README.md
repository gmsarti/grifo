Agent Stack Python (3-Tier Architecture)

Este repositório é uma implementação padrão de referência para aplicações de Agentes de IA baseada no padrão de 3 camadas (3-Tier Architecture).

Arquitetura

O projeto segue a separação lógica e física proposta para a era dos LLMs (2024-2026):

Camada de Apresentação (Presentation): Interface do usuário via Streamlit (Chat/Dashboard).

Camada de Processamento (Processing): Orquestração, raciocínio de LLM e definição de ferramentas (Agentic Logic).

Camada de Fonte de Dados (Data Source): Recuperação de contexto via RAG e conectores MCP (Model Context Protocol).

Estrutura do Projeto

app/presentation/: Interface do usuário.

app/processing/: O "cérebro" do agente e lógica de ferramentas.

app/data_source/: Conexão com bases de conhecimento e APIs externas.

Como rodar

Instale as dependências: pip install -r requirements.txt

Configure suas chaves no .env

Execute: streamlit run app/presentation/web_ui.py