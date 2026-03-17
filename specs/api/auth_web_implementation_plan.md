# Plano: Rotas de Autenticação Web (PHASE-AUTH-WEB)

Implementar login, cadastro e logout para a interface web do Grifo, usando **cookies HTTP-Only** como mecanismo de sessão. Estratégia de implementação: **Test Driven Development (TDD)** — cada ciclo segue o padrão **Red → Green → Refactor**.

---

## Contexto do Código Existente

| Componente | Status |
|---|---|
| [app/models/user.py](file:///Users/gustavosarti/Work/code/grifo/app/models/user.py) — [User](file:///Users/gustavosarti/Work/code/grifo/app/models/user.py#6-13) | ✅ Pronto |
| [app/repositories/user_repository.py](file:///Users/gustavosarti/Work/code/grifo/app/repositories/user_repository.py) — `UserRepository.get_by_email()` | ✅ Pronto |
| [app/services/auth_service.py](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py) — `AuthService.authenticate()`, [create_access_token()](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#21-34) | ✅ Pronto (parcial) |
| [app/core/config.py](file:///Users/gustavosarti/Work/code/grifo/app/core/config.py) — `SECRET_KEY`, `ALGORITHM` | ✅ Pronto |
| [app/adapters/web/templates/base.html](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/templates/base.html) — Design System (Tailwind + HTMX) | ✅ Pronto |
| `UserRepository.create_with_hash()` | ❌ Não existe |
| `AuthService.register()` | ❌ Não existe |
| Web routes de autenticação | ❌ Não existe |
| Guard de sessão para rotas web | ❌ Não existe |

---

## User Stories

### STORY-AUTH-1: Login

> **Como** pesquisador, **quero** me autenticar com email e senha **para** acessar meu workspace de forma segura.

**Critérios de Aceite:**
- Página de login com formulário (email + senha).
- Em sucesso: redirecionar para `/web/chat/1` com cookie [access_token](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#21-34) setado (HTTP-Only).
- Em falha: re-renderizar formulário com mensagem de erro inline.

---

### STORY-AUTH-2: Cadastro

> **Como** novo pesquisador, **quero** criar uma conta **para** ter acesso ao Grifo.

**Critérios de Aceite:**
- Página de registro com formulário (nome completo, email, senha, confirmação de senha).
- Em sucesso: redirecionar para `/web/login?registered=true`.
- Em falha (email duplicado, senhas divergentes): renderizar erro inline.

---

### STORY-AUTH-3: Guard de Sessão

> **Como** sistema, **quero** que rotas protegidas verifiquem o cookie **para** impedir acesso não autorizado.

**Critérios de Aceite:**
- Rotas web protegidas verificam o cookie [access_token](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#21-34).
- Usuário sem cookie válido é redirecionado para `/web/login`.
- Sidebar do [base.html](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/templates/base.html) exibe o nome real do usuário logado.

---

### STORY-AUTH-4: Logout

> **Como** pesquisador, **quero** encerrar minha sessão **para** proteger minha conta.

**Critérios de Aceite:**
- `POST /web/logout` apaga o cookie [access_token](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#21-34).
- Redirecionar para `/web/login` após logout.
- Botão de logout visível na sidebar.

---

## Estratégia TDD — Ciclos Red → Green → Refactor

Cada ciclo cobre uma camada da arquitetura. A ordem vai do **core** (domínio) para a **periferia** (rotas e templates).

---

### Ciclo 1 — Repositório: `create_with_hash()`
**Camada:** Persistência

**🔴 Red — Escrever o teste primeiro**

Arquivo: [tests/unit/repositories/test_user_repository.py](file:///Users/gustavosarti/Work/code/grifo/tests/unit/repositories/test_user_repository.py)

```python
async def test_create_user_with_hash_stores_hashed_password(db_session):
    repo = UserRepository(db_session)
    user = await repo.create_with_hash("a@b.com", "Ana", "senha123")
    assert user.hashed_password != "senha123"
    assert user.email == "a@b.com"
```

**🟢 Green — Implementar o mínimo**

Arquivo: [app/repositories/user_repository.py](file:///Users/gustavosarti/Work/code/grifo/app/repositories/user_repository.py)
- Adicionar `create_with_hash(email, full_name, password)` que usa [get_password_hash()](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#17-19).

**🔵 Refactor**
- Mover import de [get_password_hash](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#17-19) para o repositório ou manter no service? Avaliar acoplamento.

---

### Ciclo 2 — Service: `AuthService.register()`
**Camada:** Domínio / Negócio

**🔴 Red — Escrever o teste primeiro**

Arquivo: [tests/unit/services/test_auth_service.py](file:///Users/gustavosarti/Work/code/grifo/tests/unit/services/test_auth_service.py)

```python
async def test_register_creates_user(mock_user_repo):
    mock_user_repo.get_by_email.return_value = None
    service = AuthService(mock_user_repo)
    await service.register("a@b.com", "Ana", "senha123")
    mock_user_repo.create_with_hash.assert_called_once_with("a@b.com", "Ana", "senha123")

async def test_register_raises_if_email_exists(mock_user_repo):
    mock_user_repo.get_by_email.return_value = MagicMock()  # usuario já existe
    service = AuthService(mock_user_repo)
    with pytest.raises(ValueError, match="Email já cadastrado"):
        await service.register("a@b.com", "Ana", "senha123")
```

**🟢 Green — Implementar o mínimo**

Arquivo: [app/services/auth_service.py](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py)
- Adicionar método `register()` ao [AuthService](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#36-47).

**🔵 Refactor**
- Verificar se faz sentido mover [get_password_hash](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#17-19) inteiramente para o repositório.

---

### Ciclo 3 — Dependency: `get_current_web_user()`
**Camada:** Infraestrutura Web

**🔴 Red — Escrever o teste primeiro**

Arquivo: `tests/unit/web/test_web_deps.py`

```python
def test_get_current_user_returns_none_without_cookie(mock_request):
    mock_request.cookies = {}
    user = await get_optional_current_web_user(mock_request, mock_db)
    assert user is None

def test_get_current_user_returns_user_with_valid_cookie(mock_request, mock_db):
    token = create_access_token({"sub": "a@b.com"})
    mock_request.cookies = {"access_token": token}
    mock_db.get_by_email.return_value = MagicMock(email="a@b.com")
    user = await get_optional_current_web_user(mock_request, mock_db)
    assert user.email == "a@b.com"
```

**🟢 Green — Implementar o mínimo**

Arquivo: [NEW] `app/adapters/web/deps.py`
- `get_optional_current_web_user(request, db)` → decodifica JWT do cookie, busca user no repo.
- `get_current_web_user(user)` → lança redirect se `None`.

**🔵 Refactor**
- Extrair lógica de decodificação JWT para função utilitária em `app/core/security.py` se não existir.

---

### Ciclo 4 — Rotas: Login, Register, Logout + Templates
**Camada:** Adapter Web (Rotas + Templates)

**🔴 Red — Escrever os testes primeiro**

Arquivo: `tests/web/test_auth_web.py`

| Teste | O que verifica |
|---|---|
| `test_get_login_page` | `GET /web/login` → 200, formulário HTML presente |
| `test_get_register_page` | `GET /web/register` → 200, formulário HTML presente |
| `test_post_login_success` | Mock [authenticate()](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#40-47) → 303, `Set-Cookie: access_token` |
| `test_post_login_failure` | Mock retorna `None` → 200, mensagem de erro no HTML |
| `test_post_register_success` | Mock `register()` → 303 redirect para `/web/login` |
| `test_post_register_duplicate` | Mock lança `ValueError` → 200, mensagem de erro |
| `test_post_logout` | `POST /web/logout` → 303, cookie com `max_age=0` |
| `test_chat_unauthenticated_redirect` | `GET /web/chat/1` sem cookie → 303 para `/web/login` |

**🟢 Green — Implementar o mínimo** (nesta ordem)

1. **[NEW] `app/adapters/web/routes/auth.py`**

   | Método | Rota | Ação |
   |---|---|---|
   | `GET` | `/web/login` | Renderiza `pages/login.html` |
   | `POST` | `/web/login` | Valida → seta cookie → redirect ou erro |
   | `GET` | `/web/register` | Renderiza `pages/register.html` |
   | `POST` | `/web/register` | Cria usuário → redirect ou erro |
   | `POST` | `/web/logout` | Apaga cookie → redirect `/web/login` |

   Estratégia do cookie:
   ```python
   response.set_cookie(
       key="access_token",
       value=token,
       httponly=True,
       max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
       samesite="lax",
   )
   ```

2. **[NEW] `app/adapters/web/templates/auth_base.html`** — Layout sem sidebar (logo + card central), mesmo design system.

3. **[NEW] `app/adapters/web/templates/pages/login.html`** — Campos email/senha, área de erro, link para `/web/register`.

4. **[NEW] `app/adapters/web/templates/pages/register.html`** — Campos full_name/email/password/password_confirm, área de erro, link para `/web/login`.

5. **[MODIFY] [app/adapters/web/routes/chat.py](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/routes/chat.py)** — Adicionar `Depends(get_current_web_user)` nas rotas protegidas.

6. **[MODIFY] [app/adapters/web/templates/base.html](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/templates/base.html)** — Exibir `current_user.full_name` e botão de logout na sidebar.

7. **[MODIFY] [app/adapters/web/main.py](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/main.py)** — Registrar `auth_router`.

**🔵 Refactor**
- Extrair mensagens de erro do HTML para constantes ou dicionários reutilizáveis.
- Validar `password_confirm == password` no service ou na rota (decidir fronteira).

---

## Ordem de Execução (Sequência Completa)

```
Ciclo 1: 🔴 test_user_repository  →  🟢 create_with_hash()         →  🔵 refactor
Ciclo 2: 🔴 test_auth_service     →  🟢 AuthService.register()     →  🔵 refactor
Ciclo 3: 🔴 test_web_deps         →  🟢 deps.py (cookie guard)     →  🔵 refactor
Ciclo 4: 🔴 test_auth_web.py      →  🟢 auth.py + templates        →  🔵 refactor
```

**Comando para rodar após cada ciclo:**
```bash
uv run pytest tests/ -v --tb=short
```

---

## Verificação Final

```bash
# Todos os testes de autenticação web
uv run pytest tests/web/test_auth_web.py -v

# Todos os testes do projeto
uv run pytest tests/ -v
```

**Manual no navegador:**
1. `uv run python main.py`
2. `GET /web/chat/1` sem cookie → deve redirecionar para `/web/login`
3. Login com credenciais inválidas → erro inline
4. Registrar novo usuário → redirect para login
5. Login com novo usuário → chat com nome na sidebar
6. Logout → volta para `/web/login`, cookie apagado
