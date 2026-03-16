# Automação de Qualidade e Testes

Este documento explica como funciona a automação de qualidade (Ruff) e testes (Pytest) no projeto e como você pode rodá-los manualmente.

## 1. Local (Git Hooks)

Configuramos o `pre-commit` para rodar o Ruff automaticamente antes de cada `git commit`. Se houver erros que o Ruff não consiga corrigir sozinho, o commit será bloqueado para que você possa revisar.

### Instalação (Uma única vez)
Para ativar os ganchos no seu computador:
```bash
uv run pre-commit install
```

### Rodar manualmente
Se quiser rodar todos os hooks em todos os arquivos sem fazer um commit:
```bash
uv run pre-commit run --all-files
```

---

## 2. Nuvem (GitHub Actions)

Toda vez que você fizer um `push` ou abrir um `Pull Request` para a branch `main`, o GitHub executará automaticamente:
1. Verificação de Linting (`ruff check`)
2. Verificação de Formatação (`ruff format --check`)
3. Execução de todos os testes unitários e de integração (`pytest`)

Você pode ver o status (passou ou falhou) diretamente na aba **Actions** do seu repositório no GitHub.

---

## 3. Comandos Úteis (Manuais)

Se você preferir rodar os comandos individualmente sem usar o sistema de hooks:

### Ruff (Linting e Formatação)
```bash
# Apenas verificar erros
uv run ruff check .

# Verificar e tentar corrigir automaticamente (incluindo variáveis não usadas)
uv run ruff check --fix --unsafe-fixes .

# Formatar o código (espaços, quebras de linha, etc)
uv run ruff format .
```

### Pytest (Testes)
```bash
# Rodar todos os testes
uv run pytest

# Rodar um arquivo específico
uv run pytest tests/unit/test_memory.py

# Rodar testes e ver o log/output (útil para debug)
uv run pytest -s
```

---

## 4. Configurando Variáveis de Ambiente no GitHub

Para que os testes rodem no GitHub Actions, você precisa cadastrar suas chaves de API como **Secrets**.

### Passo a passo:
1. No seu repositório no GitHub, clique na aba **Settings** (Configurações).
2. No menu lateral esquerdo, clique em **Secrets and variables** -> **Actions**.
3. Clique no botão verde **New repository secret**.
4. Adicione as seguintes chaves (conforme o seu `.env`):
   - `OPENAI_API_KEY`
   - `DEEPSEEK_API_KEY`
   - `TAVILY_API_KEY`
   - `LANGSMITH_API_KEY`
5. Clique em **Add secret** para cada uma.

O workflow do GitHub Actions já está configurado para ler esses nomes e injetá-los automaticamente durante a execução do comando `uv run pytest`.
