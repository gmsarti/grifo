# Manifesto de Testes — Projeto Grifo

Este documento define os princípios, padrões e convenções que devem guiar o desenvolvimento e manutenção de testes no Grifo. Todo teste novo deve estar alinhado com estas diretrizes.

---

## 1. Princípios Gerais

### 1.1 Testes são código de primeira classe
Testes merecem o mesmo cuidado que o código de produção: sem duplicação desnecessária, sem lógica complexa enterrada em helpers opacos, e com nomes que comunicam intenção.

### 1.2 Um teste deve falhar por um único motivo
Cada teste verifica uma coisa. Se um teste falha, deve ser óbvio o que quebrou. Testes que verificam múltiplos comportamentos devem ser divididos.

### 1.3 Testes não devem depender de ordem de execução
Cada teste deve ser capaz de rodar de forma isolada. Sem estado global compartilhado entre testes, sem dependência de que outro teste rodou antes.

### 1.4 Prefira clareza à brevidade
Um teste verboso mas legível é melhor que um teste conciso mas misterioso. O nome do teste é sua documentação primária.

---

## 2. Estrutura de Diretórios

```
tests/
├── conftest.py                  # Fixtures globais: engine, db_session, client, vector_manager
├── unit/
│   ├── conftest.py              # Fixtures de unit: mock_llms, mock_store_manager, mock_history_db
│   ├── repositories/
│   │   ├── conftest.py          # Fixtures de repositório: test_user, test_project
│   │   ├── test_user_repository.py
│   │   ├── test_project_repository.py
│   │   └── test_chat_repository.py
│   ├── services/
│   │   ├── test_auth_service.py
│   │   ├── test_project_service.py
│   │   └── test_rag_service.py
│   ├── web/
│   │   └── test_web_deps.py
│   ├── test_agent.py
│   ├── test_agent_graph_structure.py
│   ├── test_agent_schemas.py
│   ├── test_chains.py
│   ├── test_bm25.py
│   ├── test_bm25_rebuild.py
│   ├── test_hybrid.py
│   ├── test_loaders.py
│   ├── test_loaders_validation.py
│   ├── test_memory.py
│   ├── test_observability.py
│   ├── test_populate_db.py
│   ├── test_rag_chains.py
│   ├── test_text_processor.py
│   ├── test_tool_executor.py
│   └── test_web_loaders.py
├── integration/
│   ├── conftest.py              # Fixtures de integração: auth_token
│   ├── api/
│   │   ├── test_auth_api.py
│   │   └── test_project_api.py
│   ├── web/
│   │   └── test_base_layout.py
│   ├── test_agent_flow.py
│   ├── test_api_ingestion.py
│   ├── test_e2e_demo.py
│   ├── test_memory_persistence.py
│   ├── test_rag_full_flow.py
│   └── test_vector_ingestion.py
└── web/
    ├── test_auth_web.py
    └── test_chat_web.py
```

**Regra:** nenhum arquivo `test_*.py` deve existir diretamente em `tests/` (raiz). Testes devem estar em `unit/`, `integration/` ou `web/`.

---

## 3. Fixtures

### 3.1 Hierarquia de conftest.py

Cada nível de diretório tem seu próprio `conftest.py` contendo apenas as fixtures relevantes para aquele escopo:

| Arquivo | Conteúdo |
|---|---|
| `tests/conftest.py` | `engine`, `db_session`, `client` (httpx), `vector_manager` |
| `tests/unit/conftest.py` | `mock_llms`, `mock_store_manager`, `mock_history_db` |
| `tests/unit/repositories/conftest.py` | `test_user`, `test_project` |
| `tests/integration/conftest.py` | `auth_token` |

### 3.2 Escopo de fixtures

- Use `scope="session"` apenas para recursos caros e imutáveis (ex: criação do schema do banco).
- Use `scope="function"` (padrão) para tudo que possui estado mutável.
- Nunca compartilhe estado mutável entre testes via fixture de sessão.

### 3.3 Cleanup garantido

Fixtures que abrem recursos devem usar `yield` + cleanup, nunca `return`:

```python
# correto
@pytest.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

# errado — cleanup não garantido se o teste falhar
def test_algo():
    app.dependency_overrides[get_db] = ...
    # ... teste ...
    app.dependency_overrides.clear()  # não roda se o teste lançar exceção
```

### 3.4 Não duplique fixtures entre arquivos

Se uma fixture é usada em mais de um arquivo de teste, ela pertence ao `conftest.py` do ancestral comum. Fixtures locais são permitidas apenas quando são específicas de um único arquivo de teste.

---

## 4. Testes Assíncronos

### 4.1 Não use `@pytest.mark.asyncio`

O projeto usa `asyncio_mode = auto` em `pytest.ini`. O decorator é redundante e deve ser omitido.

### 4.2 Não use `@pytest.mark.anyio`

Use exclusivamente o backend asyncio nativo do pytest-asyncio. O uso de `anyio` é inconsistente com o restante da suite.

### 4.3 Regra geral

```python
# correto
async def test_minha_funcao():
    resultado = await minha_funcao()
    assert resultado == esperado

# errado
@pytest.mark.asyncio
async def test_minha_funcao():
    ...
```

---

## 5. Nomenclatura

### 5.1 Nome do arquivo

`test_<modulo_ou_componente>.py` — reflete o que está sendo testado, não o tipo de teste.

### 5.2 Nome da função de teste

Formato: `test_<comportamento>_<condicao>_<resultado_esperado>` (use o que for mais legível).

```python
# bons exemplos
test_authenticate_wrong_password_returns_none()
test_save_fact_without_thread_id_excludes_thread_from_namespace()
test_register_raises_if_email_exists()

# ruim
test_auth()
test_caso2()
test_memory_2()
```

### 5.3 Classes de teste

Use classes (`TestNomeDoComponente`) apenas quando agrupar testes que compartilham fixtures ou contexto via `@pytest.fixture` de método. Não use classes apenas por organização cosmética.

---

## 6. Mocks e Patches

### 6.1 Patch no ponto de uso, não na origem

```python
# correto — patch onde o símbolo é importado/usado
@patch("app.processing.agent.get_first_responder")

# errado — patch na definição original
@patch("app.processing.chains.get_first_responder")
```

### 6.2 Prefira `pytest-mock` (mocker) a `unittest.mock.patch` como decorator

`mocker.patch()` tem cleanup automático e não aninha decorators:

```python
# correto
def test_algo(mocker):
    mocker.patch("app.processing.agent.get_first_responder", return_value=mock_chain)

# aceitável mas mais verboso
@patch("app.processing.agent.get_first_responder")
def test_algo(mock_first_responder):
    ...
```

### 6.3 Não mocke o que você não precisa

Mocke apenas as dependências externas (LLM, banco, HTTP). Deixe o código interno de produção rodar de verdade sempre que possível.

---

## 7. Tipos de Teste e Limites

### 7.1 Testes unitários (`tests/unit/`)

- Testam uma unidade isolada (função, classe, método).
- Sem I/O real: sem banco, sem HTTP externo, sem LLM.
- Devem ser rápidos (< 100ms cada).
- Mocks são permitidos e esperados para dependências externas.

### 7.2 Testes de integração (`tests/integration/`)

- Testam a colaboração entre componentes.
- Usam banco em memória real (`sqlite+aiosqlite:///:memory:`).
- LLMs e APIs externas devem ser mockados.
- Permitem I/O local (arquivos temporários, banco em memória).

### 7.3 Testes web (`tests/web/`)

- Testam rotas HTTP do adaptador web (HTMX/HTML).
- Usam `httpx.AsyncClient` com `ASGITransport`.
- Dependências de autenticação e serviços devem ser mockadas via `dependency_overrides`.

### 7.4 Testes de contrato de prompt (`@pytest.mark.prompt_contract`)

- Verificam o conteúdo textual de prompts de LLM.
- São frágeis por natureza — qualquer refatoração de prompt pode quebrá-los.
- Devem ser marcados com `@pytest.mark.prompt_contract` para poder ser excluídos em runs rápidos: `pytest -m "not prompt_contract"`.
- Vivem em `tests/unit/test_chains.py`.

---

## 8. Cliente HTTP nos Testes

Padrão único para todos os testes que fazem requisições HTTP à aplicação:

```python
# padrão — usar o fixture `client` do conftest
async def test_minha_rota(client):
    response = await client.get("/api/v1/endpoint")
    assert response.status_code == 200
```

- Nunca instancie `TestClient` (síncrono) em testes novos.
- Nunca crie um `AsyncClient` local dentro do teste; use o fixture.
- A única exceção é quando o teste precisa de configuração de cliente muito específica (ex: header diferente por teste).

---

## 9. Banco de Dados nos Testes

- O banco de testes é sempre `sqlite+aiosqlite:///:memory:`.
- A engine é criada uma vez por sessão (`scope="session"`).
- Cada teste recebe uma sessão com rollback automático ao final (`scope="function"`).
- Nunca use o banco de produção ou arquivos SQLite persistentes em testes automatizados.

---

## 10. O que NÃO fazer

| Proibido | Alternativa |
|---|---|
| `@pytest.mark.asyncio` em funções | Remova o decorator; `asyncio_mode = auto` resolve |
| `@pytest.mark.anyio` | Use asyncio nativo |
| `app.dependency_overrides` gerenciado dentro do teste | Encapsule em fixture com `yield` |
| Fixtures idênticas em múltiplos arquivos | Mova para o `conftest.py` pai |
| Testes em `tests/` diretamente (fora de subdiretórios) | Coloque em `unit/`, `integration/` ou `web/` |
| `TestClient` síncrono em testes novos | Use `httpx.AsyncClient` via fixture `client` |
| `time.sleep()` em testes | Use mocks ou eventos assíncronos |
| Assertar múltiplos comportamentos não relacionados | Divida em testes separados |
