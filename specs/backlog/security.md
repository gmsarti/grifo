# Backlog — Segurança

Este arquivo contém o detalhamento técnico de todas as tarefas relacionadas à segurança do sistema.

---

### ✅ [B-001] SECRET_KEY com valor padrão inseguro

- **Tipo**: Segurança
- **Prioridade**: Crítica
- **Área**: `app/core/`

**Problema:**
`config.py` define `SECRET_KEY: str = "supersecretkey"`. Se o arquivo `.env` não declarar essa variável, todos os JWTs são assinados com uma chave trivial e publicamente conhecida. Qualquer pessoa pode forjar tokens de autenticação válidos.

**Solução proposta:**
Remover o valor padrão, tornando a variável obrigatória. A aplicação deve recusar a iniciar se `SECRET_KEY` não estiver definida no ambiente — ou, como segunda opção, validar que o valor não é o padrão e lançar um erro na startup.

```python
# config.py
SECRET_KEY: str  # sem default — obriga definição no .env

# main.py (ou lifespan)
if settings.SECRET_KEY in ("supersecretkey", "", "changeme"):
    raise RuntimeError("SECRET_KEY insegura. Defina um valor forte no .env.")
```

**Arquivos afetados:**
- `app/core/config.py`
- `app/main.py` (validação na startup)
- `.env.example` (documentar que o valor é obrigatório)

**Critério de aceite:**
- A aplicação não inicia sem `SECRET_KEY` definida no `.env`
- Testes de startup validam o comportamento
- `.env.example` possui instrução clara sobre como gerar uma chave segura (`openssl rand -hex 32`)

---

### ✅ [B-006] Rate limiting ausente no endpoint de chat

- **Tipo**: Segurança / Melhoria
- **Prioridade**: Média
- **Área**: `app/adapters/api/`

**Problema:**
`POST /api/v1/chat` chama LLMs caros (GPT-4o) sem nenhuma proteção contra abuso. Um único usuário autenticado pode disparar centenas de requisições e gerar custos inesperados.

**Solução proposta:**
Adicionar rate limiting por usuário usando `slowapi` (integração nativa com FastAPI):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat")
@limiter.limit("20/minute")
async def chat_endpoint(...):
    ...
```

Tornar os limites configuráveis via `.env` (`RATE_LIMIT_CHAT=20/minute`).

**Arquivos afetados:**
- `app/adapters/api/` (rotas de chat)
- `app/core/config.py`
- `pyproject.toml`

**Critério de aceite:**
- Requisições acima do limite retornam `429 Too Many Requests`
- Limite é configurável por variável de ambiente
- Testes verificam o comportamento de throttling

---

### ✅ [B-010] Validação e sanitização do `system_prompt`

- **Tipo**: Segurança
- **Prioridade**: Média
- **Área**: `app/schemas/`, `app/adapters/api/`

**Problema:**
Via API, um usuário pode definir um `system_prompt` com conteúdo arbitrariamente longo ou com tentativas de prompt injection para contornar o comportamento esperado do agente.

**Solução proposta:**
- Definir tamanho máximo para `system_prompt` (ex: 2000 caracteres) via validador Pydantic
- Documentar claramente que o campo é confiável apenas para usuários administradores do projeto

```python
from pydantic import field_validator

class ProjectCreate(BaseModel):
    system_prompt: str | None = None

    @field_validator("system_prompt")
    def validate_system_prompt(cls, v):
        if v and len(v) > 2000:
            raise ValueError("system_prompt não pode exceder 2000 caracteres")
        return v
```

**Arquivos afetados:**
- `app/schemas/project.py`

**Critério de aceite:**
- `system_prompt` acima do limite retorna `422 Unprocessable Entity`
- Testes cobrem casos de borda (None, vazio, no limite, acima do limite)

---

### ❌ [B-017] Verificação de Vulnerabilidades no Código (SAST)

- **Tipo**: Segurança
- **Prioridade**: Média
- **Área**: Desenvolvimento / Infra

**Problema:**
Atualmente não há uma ferramenta que analise automaticamente o código em busca de padrões inseguros (ex: uso de `shell=True`, geração de números aleatórios fracos, etc).

**Solução proposta:**
Integrar o **Bandit** ao workflow de desenvolvimento.
1. Adicionar `bandit` às dependências de desenvolvimento.
2. Ativar as regras de segurança no Ruff (`"S"`).
3. Adicionar hook de `bandit` no `pre-commit`.

**Arquivos afetados:**
- `pyproject.toml`
- `.pre-commit-config.yaml`

**Critério de aceite:**
- `pre-commit run bandit` detecta problemas de segurança conhecidos
- Ruff reporta avisos da categoria `S` (flake8-bandit)

---

### ❌ [B-018] Auditoria de Dependências (SCA)

- **Tipo**: Segurança
- **Prioridade**: Média
- **Área**: Dependências

**Problema:**
Dependências de terceiros podem conter vulnerabilidades conhecidas (CVEs). Sem uma auditoria automática, o projeto corre o risco de usar bibliotecas inseguras.

**Solução proposta:**
Implementar o **Safety** para auditar o `uv.lock`.
1. Adicionar `safety` às dependências de dev.
2. Criar um workflow que exporta as dependências e roda o scan.

**Arquivos afetados:**
- `pyproject.toml`
- `.github/workflows/security.yml`

**Critério de aceite:**
- O comando de auditoria falha se houver dependências com vulnerabilidades críticas conhecidas.

---

### ❌ [B-019] Prevenção de Vazamento de Credenciais

- **Tipo**: Segurança
- **Prioridade**: Alta
- **Área**: Segurança

**Problema:**
O projeto utiliza múltiplas chaves de API (OpenAI, Tavily). Existe um risco crítico de desenvolvedores comitarem acidentalmente o arquivo `.env` ou hardcoded chaves no código.

**Solução proposta:**
Implementar o **detect-secrets** no pipeline de pré-commit.
1. Gerar um baseline de segredos permitidos.
2. Configurar o hook para bloquear commits que contenham novos segredos não mapeados.

**Arquivos afetados:**
- `.pre-commit-config.yaml`
- `.secrets.baseline` (novo)

**Critério de aceite:**
- Tentar comitar uma string que pareça uma chave de API bloqueia o commit localmente.

---

### ❌ [B-020] Pipeline de Segurança Contínua (GitHub Actions)

- **Tipo**: Melhoria / Segurança
- **Prioridade**: Média
- **Área**: CI/CD

**Problema:**
As verificações de segurança dependem de o desenvolvedor rodar os comandos localmente. Se o pre-commit for bypassado, código inseguro chega ao repositório.

**Solução proposta:**
Criar um workflow no GitHub Actions que execute todas as ferramentas de segurança (Ruff, Bandit, Safety) em cada Push ou Pull Request.

**Arquivos afetados:**
- `.github/workflows/security.yml`

**Critério de aceite:**
- PRs que violam as regras de segurança mostram falha no status check do GitHub.
