# Especificação: Reflexion Agent

Este documento define a arquitetura e o funcionamento do **Reflexion Agent**, um agente capaz de realizar buscas no Vector Store e aprimorar iterativamente suas respostas através de um ciclo de reflexão e crítica.

## Arquitetura e Fluxo de Trabalho

O agente utiliza um padrão de "Reflexão" (Self-Correction) para garantir que a resposta final seja precisa, fundamentada e livre de alucinações.

### 1. Grafo de Estados (LangGraph)

O fluxo é gerenciado por uma máquina de estados com os seguintes nós:

- **Node: Draft:** Gera a resposta inicial (~250 palavras) e a primeira reflexão.
- **Node: Execute Tools:** Executa as buscas recomendadas pelo agente para complementar a informação.
- **Node: Revise:** Reescreve a resposta com base no feedback e nos novos dados coletados.
- **Edge: Event Loop:** Controla o ciclo de repetição baseado no número de visitas às ferramentas (`MAX_ITERATIONS = 2`).

### 2. Estrutura de Mensagens e Estado

Utiliza `MessagesState` do LangGraph para manter o histórico de interações, permitindo que o revisor acesse tanto o rascunho anterior quanto as críticas.

## Camada de Serviço: AgentOrchestrator

Para expor o grafo de forma limpa, será implementada uma classe `AgentOrchestrator` em `app/processing/agent.py`:

- **Função:** Encapsular a lógica de inicialização do compilador do LangGraph e gerenciar o `thread_id`.
- **Interface:** Expor o método `async def process_message(self, message: str, thread_id: str = None) -> ChatResponse`.
- **Orquestração:** O `AgentOrchestrator` deve injetar o `VectorStoreManager` como uma ferramenta dentro do fluxo do grafo.

## Definições Técnicas

### 1. Schemas Pydantic (Output Structuring)

Para garantir que o agente forneça críticas estruturadas, utilizamos os seguintes modelos:

```python
class Reflection(BaseModel):
    missing: str  # O que falta na resposta
    superfluous: str  # O que é desnecessário

class AnswerQuestion(BaseModel):
    answer: str
    reflection: Reflection
    search_queries: List[str]  # queries para busca no Vector Store/Web

class ReviseAnswer(AnswerQuestion):
    references: List[str]  # Fontes utilizadas
```

### 2. Estratégia de Prompts

Os prompts são modulares (`ChatPromptTemplate.partial`):

- **Base:** Define o papel de "Pesquisador Especialista" e a instrução de ser "severo na crítica".
- **Draft:** Instrução para resposta detalhada inicial.
- **Revise:** Instrução para usar a crítica anterior para remover supérfluos e adequar o tom.

## Integração com Vector Store

- O nó `execute_tools` utiliza uma ferramenta unificada de busca (`SearchTool`).
- **Smart Search:** Esta ferramenta chama o método `search` do `VectorStoreManager`.
- **Fallback Decidido:** A busca web (ex: Tavily) ocorrerá **internamente** no fluxo de busca do Vector Store se o `retrieval_grader` indicar que os documentos recuperados são irrelevantes (CRAG). Isso simplifica a lógica do agente, que sempre recebe o "melhor contexto disponível".

## Gestão de Memória

O agente diferencia entre memória de curto prazo (dentro da sessão) e memória de longo prazo (persistente entre sessões).

### 1. Curto Prazo (Conversational Memory)

- **Implementação:** `ConversationBufferMemory` com vectorstore **ChromaDB**.
- **Objetivo:** Realizar RAG sobre o histórico recente da conversa atual para manter o contexto sem sobrecarregar a janela de contexto do LLM com mensagens irrelevantes.
- **Escopo:** Thread-scoped (gerenciado via `thread_id` no LangGraph).

### 2. Longo Prazo (Cross-Session Memory)

- **Implementação:** LangGraph `BaseStore` (inicialmente `InMemoryStore`, migrando para `PostgresStore`).
- **Objetivo:** Persistir fatos, preferências do usuário e aprendizados do agente entre diferentes sessões.
- **Busca:** Utiliza `store.search()` com embeddings para busca semântica de fatos relevantes ao contexto atual.

## Lista de Tasks (Backlog Detalhado)

### [PHASE 1] Estrutura e Schemas

- [ ] [TASK-1.1] Implementar schemas Pydantic (`Reflection`, `AnswerQuestion`, `ReviseAnswer`) em `schemas.py`.
- [ ] [TASK-1.2] Definir o `MessagesState` e a estrutura básica do grafo no LangGraph.
- [ ] [TASK-1.3] Criar os templates de prompt base em `chains.py` usando `partial` para injeção de tempo e instruções.

### [PHASE 2] Nós e Lógica do Grafo

- [ ] [TASK-2.1] Implementar o nó `draft_node` usando o `first_responder` chain.
- [ ] [TASK-2.2] Implementar o nó `revise_node` usando o `revisor` chain.
- [ ] [TASK-2.3] Codificar o `event_loop` para contar mensagens de ferramentas e decidir a parada.
- [ ] [TASK-2.4] Configurar o `execute_tools` usando `ToolNode` e `StructuredTool` para mapear `search_queries`.

### [PHASE 3] Integração e Refinamento

- [ ] [TASK-3.1] Integrar a busca no Vector Store (`VectorStoreManager`) dentro da ferramenta de execução.
- [ ] [TASK-3.2] Configurar o bind das ferramentas (`AnswerQuestion` e `ReviseAnswer`) aos LLMs.
- [ ] [TASK-3.3] Adicionar suporte a `MAX_ITERATIONS` configurável via variáveis de ambiente.

### [PHASE 4] Gestão de Memória (Curto e Longo Prazo)

- [ ] [TASK-4.1] Implementar `ConversationBufferMemory` com ChromaDB para histórico de mensagens.
- [ ] [TASK-4.2] Configurar `InMemoryStore` para memória de longo prazo (cross-sessões).
- [ ] [TASK-4.3] Implementar busca semântica (`store.search()`) com embeddings na memória de longo prazo.
- [ ] [TASK-4.4] Migrar de `InMemoryStore` para `PostgresStore` para persistência em produção.
- [ ] [TASK-4.5] **Suíte de Testes de Memória**:
  - Validar persistência e recuperação do histórico no ChromaDB.
  - Testar busca semântica no `BaseStore` (InMemory e Postgres).
  - Garantir o isolamento de memória por `thread_id`.

### [PHASE 5] Qualidade e Observabilidade

- [ ] [TASK-5.1] **LangSmith Tracing & Metadata**:
  - Configurar traces detalhados para cada nó (`draft`, `revise`, `execute_tools`).
  - Adicionar metadata customizada: `iteration_count`, `model_name`, `total_tokens`.
- [ ] [TASK-5.2] **Suite de Testes Unitários**:
  - Validar extração de críticas do schema `Reflection`.
  - Testar lógica de saída do `event_loop` em limites de iteração.
  - Mockar respostas de ferramentas para garantir resiliência do revisor.
- [ ] [TASK-5.3] **Avaliação de Qualidade (LLM-as-a-Judge)**:
  - Implementar um avaliador que compare o Primeiro Draft vs. Revisão Final.
  - Critérios: Alinhamento com Direitos Humanos (conforme prompt), Redução de superfluidades, Acurácia factual.
- [ ] [TASK-5.4] **Monitoramento de Custo e Performance**:
  - Rastrear latência média por ciclo de reflexão.
  - Implementar alerta/log para consumo excessivo de tokens em revisões longas.
- [ ] [TASK-5.5] **Dataset de Regressão (Golden Dataset)**:
  - Criar conjunto de 10 perguntas complexas com "gabaritos" de pontos críticos que a reflexão DEVE abordar.
  - Automatizar execução do benchmark para garantir que melhorias no prompt não causem regressão.
