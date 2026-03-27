# Tarefas de Melhoria dos Testes

Tarefas derivadas do diagnóstico da suite de testes e alinhadas com o `manifesto.md`.
Marque cada item com `[x]` ao concluir.

---

## Fase 1 — Limpeza de Marcadores Async

> Objetivo: remover ruído e unificar o padrão asyncio em toda a suite.

- [ ] **T1.1** Remover todos os `@pytest.mark.asyncio` dos arquivos de `tests/unit/`
- [ ] **T1.2** Remover todos os `@pytest.mark.asyncio` dos arquivos de `tests/integration/`
- [ ] **T1.3** Remover todos os `@pytest.mark.asyncio` dos arquivos de `tests/web/`
- [ ] **T1.4** Substituir `@pytest.mark.anyio` por nada em `tests/test_agent_chains.py` (anyio → asyncio nativo)
- [ ] **T1.5** Verificar se todos os testes async ainda passam após as remoções (`pytest --tb=short`)

---

## Fase 2 — Fixtures Compartilhadas: Repositórios

> Objetivo: eliminar `test_user` e `test_project` duplicados entre `test_project_repository.py` e `test_chat_repository.py`.

- [ ] **T2.1** Criar `tests/unit/repositories/conftest.py`
- [ ] **T2.2** Mover fixture `test_user` (cria `User` com email único via uuid) para o novo conftest
- [ ] **T2.3** Mover fixture `test_project` (cria `Project` vinculado ao `test_user`) para o novo conftest
- [ ] **T2.4** Remover as definições locais de `test_user` e `test_project` de `test_project_repository.py`
- [ ] **T2.5** Remover as definições locais de `test_user` e `test_project` de `test_chat_repository.py`
- [ ] **T2.6** Confirmar que os testes de repositório passam com as fixtures vindas do conftest

---

## Fase 3 — Fixtures Compartilhadas: Mocks de Agent

> Objetivo: eliminar a recriação de `mock_llms`, `mock_store_manager` e `mock_history_db` entre `test_agent.py`, `test_agent_flow.py` e `test_memory_persistence.py`.

- [ ] **T3.1** Criar `tests/unit/conftest.py`
- [ ] **T3.2** Extrair fixture `mock_store_manager` de `test_agent.py` para `tests/unit/conftest.py`
- [ ] **T3.3** Extrair fixture `mock_history_db` de `test_agent.py` para `tests/unit/conftest.py`
- [ ] **T3.4** Extrair fixture `mock_llms` de `test_agent.py` para `tests/unit/conftest.py`
- [ ] **T3.5** Remover as definições inline de `mock_store_manager` e `mock_history_db` de `test_agent_flow.py`
- [ ] **T3.6** Remover as definições inline equivalentes de `test_memory_persistence.py`
- [ ] **T3.7** Confirmar que `test_agent.py`, `test_agent_flow.py` e `test_memory_persistence.py` passam

---

## Fase 4 — Fixtures Compartilhadas: VectorStoreManager

> Objetivo: centralizar o mock de `Chroma + OpenAIEmbeddings` que aparece em 5+ arquivos.

- [ ] **T4.1** Adicionar fixture `vector_manager` em `tests/conftest.py` (mock de `Chroma` + `OpenAIEmbeddings` + retorno de `VectorStoreManager` configurado)
- [ ] **T4.2** Substituir a fixture local `vector_manager` de `tests/unit/test_bm25.py` pela do conftest global
- [ ] **T4.3** Substituir a fixture local `vector_manager` de `tests/unit/test_hybrid.py` pela do conftest global
- [ ] **T4.4** Substituir os `@patch` inline de Chroma/OpenAIEmbeddings em `tests/unit/test_bm25_rebuild.py` pelo fixture
- [ ] **T4.5** Substituir os `@patch` inline de Chroma/OpenAIEmbeddings em `tests/integration/test_e2e_demo.py` pelo fixture
- [ ] **T4.6** Substituir a fixture local em `tests/integration/test_vector_ingestion.py` pela do conftest global
- [ ] **T4.7** Confirmar que todos os testes de vector store passam

---

## Fase 5 — Fixtures Compartilhadas: Auth Token de Integração

> Objetivo: centralizar a sequência register → login usada nos testes de integração de API.

- [ ] **T5.1** Criar `tests/integration/conftest.py`
- [ ] **T5.2** Mover fixture `auth_token` de `tests/integration/api/test_project_api.py` para o novo conftest
- [ ] **T5.3** Refatorar `tests/integration/api/test_auth_api.py` para usar `auth_token` de fixture ao invés de inline onde aplicável
- [ ] **T5.4** Confirmar que os testes de integração de API passam

---

## Fase 6 — Reorganização de Arquivos Legados

> Objetivo: eliminar testes no topo de `tests/` e consolidar com `unit/`.

- [ ] **T6.1** Mover `tests/test_agent_schemas.py` para `tests/unit/test_agent_schemas.py`
- [ ] **T6.2** Mover `tests/test_agent_graph_structure.py` para `tests/unit/test_agent_graph_structure.py`
- [ ] **T6.3** Comparar `tests/test_agent_chains.py` com `tests/unit/test_chains.py` e identificar testes únicos
- [ ] **T6.4** Migrar testes únicos de `tests/test_agent_chains.py` para `tests/unit/test_chains.py`
- [ ] **T6.5** Deletar `tests/test_agent_chains.py` após migração completa
- [ ] **T6.6** Adicionar `__init__.py` vazio em `tests/integration/` se ausente
- [ ] **T6.7** Adicionar `__init__.py` vazio em `tests/integration/api/` se ausente
- [ ] **T6.8** Adicionar `__init__.py` vazio em `tests/integration/web/` se ausente
- [ ] **T6.9** Confirmar que `pytest --collect-only` coleta todos os testes sem erros

---

## Fase 7 — Padronizar Cliente HTTP

> Objetivo: eliminar `TestClient` síncrono e instâncias locais de `AsyncClient`.

- [ ] **T7.1** Refatorar `tests/api/test_chat_v1.py` para usar o fixture `client` do conftest (async)
- [ ] **T7.2** Refatorar `tests/api/test_management.py` para usar o fixture `client` do conftest (remover fixture local)
- [ ] **T7.3** Refatorar `tests/web/test_chat_web.py`: substituir `TestClient` síncrono por `httpx.AsyncClient`
- [ ] **T7.4** Verificar se `tests/web/test_auth_web.py` já usa `AsyncClient` e está alinhado com o padrão (ajustar se necessário)
- [ ] **T7.5** Confirmar que os testes de `tests/api/` e `tests/web/` passam

---

## Fase 8 — Robustez: dependency_overrides em Fixtures

> Objetivo: garantir cleanup de `dependency_overrides` mesmo quando testes falham.

- [ ] **T8.1** Identificar todos os locais onde `app.dependency_overrides` é manipulado dentro do corpo do teste (não em fixture)
- [ ] **T8.2** Encapsular o override de `tests/web/test_chat_web.py` em fixture com `yield` + `app.dependency_overrides.clear()`
- [ ] **T8.3** Encapsular o override de `tests/integration/test_api_ingestion.py` em fixture com `yield`
- [ ] **T8.4** Confirmar que não há `dependency_overrides` soltos em nenhum arquivo de teste

---

## Fase 9 — Marcação de Testes de Contrato de Prompt

> Objetivo: isolar testes frágeis de conteúdo de prompt para poder excluí-los em runs rápidos.

- [ ] **T9.1** Adicionar `@pytest.mark.prompt_contract` nos testes de `tests/unit/test_chains.py` que verificam strings dentro de prompts
- [ ] **T9.2** Registrar o marker `prompt_contract` em `pytest.ini` para evitar warning de marker desconhecido
- [ ] **T9.3** Documentar no `pytest.ini` (como comentário) que `pytest -m "not prompt_contract"` exclui esses testes
- [ ] **T9.4** Confirmar que `pytest -m prompt_contract` roda apenas os testes de conteúdo de prompt

---

## Verificação Final

- [ ] **TF.1** Rodar `pytest` completo e confirmar que todos os testes passam
- [ ] **TF.2** Confirmar que nenhum arquivo `test_*.py` existe diretamente em `tests/` (raiz)
- [ ] **TF.3** Confirmar que não há `@pytest.mark.asyncio` ou `@pytest.mark.anyio` em nenhum arquivo
- [ ] **TF.4** Confirmar que não há fixtures duplicadas entre arquivos de teste
- [ ] **TF.5** Confirmar que `dependency_overrides` é gerenciado apenas em fixtures (com `yield`)
