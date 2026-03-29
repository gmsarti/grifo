# Tarefas de Melhoria dos Testes

Tarefas derivadas do diagnóstico da suite de testes e alinhadas com o `manifesto.md`.
Marque cada item com `[x]` ao concluir.

---

## Fase 1 — Limpeza de Marcadores Async

> Objetivo: remover ruído e unificar o padrão asyncio em toda a suite.

- [x] **T1.1** Remover todos os `@pytest.mark.asyncio` dos arquivos de `tests/unit/`
- [x] **T1.2** Remover todos os `@pytest.mark.asyncio` dos arquivos de `tests/integration/`
- [x] **T1.3** Remover todos os `@pytest.mark.asyncio` dos arquivos de `tests/web/`
- [x] **T1.4** Substituir `@pytest.mark.anyio` por nada em `tests/test_agent_chains.py` e `tests/test_agent_graph_structure.py`
- [x] **T1.5** Verificar se todos os testes async ainda passam após as remoções — 134 passed, 0 failures

---

## Fase 2 — Fixtures Compartilhadas: Repositórios

> Objetivo: eliminar `test_user` e `test_project` duplicados entre `test_project_repository.py` e `test_chat_repository.py`.

- [x] **T2.1** Criar `tests/unit/repositories/conftest.py`
- [x] **T2.2** Mover fixture `test_user` (cria `User` com email único via uuid) para o novo conftest
- [x] **T2.3** Mover fixture `test_project` (cria `Project` vinculado ao `test_user`) para o novo conftest
- [x] **T2.4** Remover as definições locais de `test_user` e `test_project` de `test_project_repository.py`
- [x] **T2.5** Remover as definições locais de `test_user` e `test_project` de `test_chat_repository.py`
- [x] **T2.6** Confirmar que os testes de repositório passam com as fixtures vindas do conftest — 10 passed

---

## Fase 3 — Fixtures Compartilhadas: Mocks de Agent

> Objetivo: eliminar a recriação de `mock_llms`, `mock_store_manager` e `mock_history_db` entre `test_agent.py`, `test_agent_flow.py` e `test_memory_persistence.py`.

- [x] **T3.1** Criar `tests/unit/conftest.py`
- [x] **T3.2** Extrair fixture `mock_store_manager` para `tests/unit/conftest.py` (só usada em unit)
- [x] **T3.3** Extrair fixture `mock_history_db` para `tests/conftest.py` (usada em unit e integration)
- [x] **T3.4** Extrair fixture `mock_llms` para `tests/unit/conftest.py` (só usada em unit)
- [x] **T3.5** Remover as definições inline de `mock_history_db` de `test_agent_flow.py`; testes passam `mock_history_db` como parâmetro
- [x] **T3.6** Verificado `test_memory_persistence.py` — sem inline mocks das fixtures em questão
- [x] **T3.7** Confirmar que os três arquivos passam — 28 passed

---

## Fase 4 — Fixtures Compartilhadas: VectorStoreManager

> Objetivo: centralizar o mock de `Chroma + OpenAIEmbeddings` que aparece em 5+ arquivos.

- [x] **T4.1** Adicionar fixture `vector_manager` em `tests/conftest.py` (mock de Chroma + OpenAIEmbeddings + HybridRetriever)
- [x] **T4.2** Substituir a fixture local `vector_manager` de `tests/unit/test_bm25.py` pela do conftest global
- [x] **T4.3** `tests/unit/test_hybrid.py` mantém fixture local — usa `spec=BaseRetriever` e não mocka HybridRetriever; semântica diferente e incompatível com a global
- [x] **T4.4** `tests/unit/test_bm25_rebuild.py` mantém helper `_make_manager` — cada teste configura `Chroma.get()` diferente; abstração local adequada
- [x] **T4.5** Refatorar `tests/integration/test_e2e_demo.py` para usar fixture `vector_manager`; removidos patches redundantes inline
- [x] **T4.6** Substituir a fixture local de `tests/integration/test_vector_ingestion.py` pela do conftest global
- [x] **T4.7** Confirmar que todos os testes de vector store passam — 12 passed

---

## Fase 5 — Fixtures Compartilhadas: Auth Token de Integração

> Objetivo: centralizar a sequência register → login usada nos testes de integração de API.

- [x] **T5.1** Criar `tests/integration/conftest.py`
- [x] **T5.2** Mover fixture `auth_token` para o novo conftest; email atualizado para `integration_user@example.com`
- [x] **T5.3** `test_auth_api.py` testa o próprio fluxo de auth por teste — sem `auth_token` aplicável; sem alteração necessária
- [x] **T5.4** Confirmar que os testes de integração de API passam — 7 passed

---

## Fase 6 — Reorganização de Arquivos Legados

> Objetivo: eliminar testes no topo de `tests/` e consolidar com `unit/`.

- [x] **T6.1** Mover `tests/test_agent_schemas.py` para `tests/unit/test_agent_schemas.py`
- [x] **T6.2** Mover `tests/test_agent_graph_structure.py` para `tests/unit/` (removido `import pytest` sem uso)
- [x] **T6.3** Comparado: único teste exclusivo era `test_actor_prompt_template_partial`; `test_get_first_responder`, `test_get_revisor` e `test_orchestrator_initialization` eram duplicatas mais fracas
- [x] **T6.4** Migrado `test_actor_prompt_template_partial` para `tests/unit/test_chains.py`
- [x] **T6.5** Deletado `tests/test_agent_chains.py`
- [x] **T6.6** Criado `tests/integration/__init__.py`
- [x] **T6.7** Criado `tests/integration/api/__init__.py`
- [x] **T6.8** Criado `tests/integration/web/__init__.py`
- [x] **T6.9** 141 testes coletados e passando sem erros

---

## Fase 7 — Padronizar Cliente HTTP

> Objetivo: eliminar `TestClient` síncrono e instâncias locais de `AsyncClient`.

- [x] **T7.1** Refatorar `tests/api/test_chat_v1.py` para usar fixture `client` async do conftest
- [x] **T7.2** Refatorar `tests/api/test_management.py`: removida fixture local síncrona, testes tornados async
- [x] **T7.3** Refatorar `tests/web/test_chat_web.py`: `TestClient` síncrono substituído por fixture `client` async
- [x] **T7.4** `tests/web/test_auth_web.py`: removida fixture local `client`; testes já usavam async e passam a usar conftest
- [x] **T7.5** 15 passed — bonus: adicionado `asyncio_default_test_loop_scope = session` ao pytest.ini para unificar event loops e eliminar `RuntimeError: Event loop is closed`

---

## Fase 8 — Robustez: dependency_overrides em Fixtures

> Objetivo: garantir cleanup de `dependency_overrides` mesmo quando testes falham.

- [x] **T8.1** Identificados 2 testes em `test_chat_web.py` com overrides no corpo sem cleanup garantido
- [x] **T8.2** Extraídas fixtures `authenticated_client` e `rag_service_override` em `test_chat_web.py`; cleanup via `.pop()` no yield
- [x] **T8.3** `test_api_ingestion.py` já tinha override encapsulado em fixture `test_app` com `yield` + `.clear()` — sem alteração necessária
- [x] **T8.4** Todos os `dependency_overrides` estão dentro de fixtures; nenhum solto no corpo de testes

---

## Fase 9 — Marcação de Testes de Contrato de Prompt

> Objetivo: isolar testes frágeis de conteúdo de prompt para poder excluí-los em runs rápidos.

- [x] **T9.1** Adicionar `@pytest.mark.prompt_contract` nos testes de `tests/unit/test_chains.py` que verificam strings dentro de prompts
- [x] **T9.2** Registrar o marker `prompt_contract` em `pytest.ini` para evitar warning de marker desconhecido
- [x] **T9.3** Documentar no `pytest.ini` (como comentário) que `pytest -m "not prompt_contract"` exclui esses testes
- [x] **T9.4** Confirmar que `pytest -m prompt_contract` roda apenas os testes de conteúdo de prompt — 7/146 coletados

---

## Verificação Final

- [x] **TF.1** Rodar `pytest` completo e confirmar que todos os testes passam — 146 passed, 0 failures
- [x] **TF.2** Confirmar que nenhum arquivo `test_*.py` existe diretamente em `tests/` (raiz)
- [x] **TF.3** Confirmar que não há `@pytest.mark.asyncio` ou `@pytest.mark.anyio` em nenhum arquivo
- [x] **TF.4** Confirmar que não há fixtures duplicadas entre arquivos de teste
- [x] **TF.5** Confirmar que `dependency_overrides` é gerenciado apenas em fixtures (com `yield`)
