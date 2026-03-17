# Walkthrough - Implementação de Autenticação Web

Implementação completa de login, cadastro e logout para a interface web do Grifo, utilizando **cookies HTTP-Only** e seguindo a metodologia **TDD**.

## Mudanças Realizadas

### 1. Núcleo e Segurança
- **[NEW] [security.py](file:///Users/gustavosarti/Work/code/grifo/app/core/security.py)**: Centralização da lógica de hashing de senhas e geração de tokens JWT.
- **[MODIFY] [user_repository.py](file:///Users/gustavosarti/Work/code/grifo/app/repositories/user_repository.py)**: Adicionado método [create_with_hash](file:///Users/gustavosarti/Work/code/grifo/app/repositories/user_repository.py#51-63) para persistência segura de novos usuários.
- **[MODIFY] [auth_service.py](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py)**: Adicionado método [register](file:///Users/gustavosarti/Work/code/grifo/app/services/auth_service.py#22-28) com validação de email duplicado.

### 2. Infraestrutura Web
- **[NEW] [deps.py](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/deps.py)**: Dependências FastAPI para extrair e validar o usuário a partir do cookie de sessão.
- **[NEW] [auth.py](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/routes/auth.py)**: Rotas para as páginas e ações de autenticação.
- **[MODIFY] [chat.py](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/routes/chat.py)**: Proteção das rotas de chat com obrigatoriedade de login.

### 3. Interface (Modern Scriptorium)
- **[NEW] [auth_base.html](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/templates/auth_base.html)**: Layout minimalista para páginas de auth.
- **[NEW] [login.html](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/templates/pages/login.html)**: Tela de login com feedback de erro.
- **[NEW] [register.html](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/templates/pages/register.html)**: Tela de cadastro.
- **[MODIFY] [base.html](file:///Users/gustavosarti/Work/code/grifo/app/adapters/web/templates/base.html)**: Sidebar agora exibe o nome do pesquisador e botão de logout.

## Verificação Submetida

### Testes Automatizados
Todos os 107 testes do projeto estão passando, incluindo as novas baterias:
- [tests/unit/repositories/test_user_repository.py](file:///Users/gustavosarti/Work/code/grifo/tests/unit/repositories/test_user_repository.py)
- [tests/unit/services/test_auth_service.py](file:///Users/gustavosarti/Work/code/grifo/tests/unit/services/test_auth_service.py)
- [tests/unit/web/test_web_deps.py](file:///Users/gustavosarti/Work/code/grifo/tests/unit/web/test_web_deps.py)
- [tests/web/test_auth_web.py](file:///Users/gustavosarti/Work/code/grifo/tests/web/test_auth_web.py)

### Demonstração Visual

````carousel
# Página de Login
A página de login segue a estética de "Scriptorium", com tons de pergaminho e tipografia clássica.
<!-- slide -->
# Registro de Usuário
O formulário de registro inclui validações de senha e redirecionamento inteligente após o sucesso.
<!-- slide -->
# Sidebar Autenticada
A barra lateral agora exibe o nome real do usuário logado e permite o encerramento da sessão via botão de logout.
````

## Como Testar Manualmente
1. Inicie o servidor: `uv run python main.py`
2. Tente acessar `http://localhost:8000/web/chat/1` -> Você será redirecionado para o Login.
3. Cadastre-se em `/web/register`.
4. Faça login com as novas credenciais.
5. Verifique seu nome na sidebar e o funcionamento do logout.
