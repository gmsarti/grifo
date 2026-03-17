# Automação Ágil (Ruff + Testes)

Este projeto usa uma automação simplificada focada em **estudo e agilidade**.

## 1. Local (Git Hooks)

O `pre-commit` cuida da limpeza básica antes de cada commit.

- **Instalação**: `uv run pre-commit install`
- **O que ele faz**: Roda o Ruff para corrigir erros automáticos e formatar o código. Se algo estiver muito errado, ele te avisa.

## Qualidade e Testes (Manual)

Como o CI foi desativado, você pode rodar as ferramentas de qualidade manualmente quando desejar.

### 1. Limpeza e Formatação (Ruff)

```bash
# Corrigir erros automáticos e organizar imports
uv run ruff check --fix .

# Formatar o código (espaços, aspas, etc)
uv run ruff format .
```

### 2. Testes (Pytest)

```bash
# Rodar todos os testes unitários
uv run pytest tests/unit
```

*(Opcional) Se você ainda quiser que o Ruff rode automaticamente antes de cada commit no seu computador, você pode manter o `pre-commit` instalado com `uv run pre-commit install`.*
