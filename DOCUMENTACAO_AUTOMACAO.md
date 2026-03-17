# Automação Ágil (Ruff + Testes)

Este projeto usa uma automação simplificada focada em **estudo e agilidade**.

## 1. Local (Git Hooks)

O `pre-commit` cuida da limpeza básica antes de cada commit.

- **Instalação**: `uv run pre-commit install`
- **O que ele faz**: Roda o Ruff para corrigir erros automáticos e formatar o código. Se algo estiver muito errado, ele te avisa.

## 2. GitHub CI (Simplificado)

Toda vez que você enviar código para o GitHub:
1. **Linting**: O Ruff verifica se não há erros críticos (variáveis não usadas, bugs lógicos).
2. **Testes Unitários**: Apenas os testes de unidade (que não dependem de banco de dados ou APIs reais) são executados para garantir que a lógica base está correta.

Isso garante que o projeto "funciona" sem a burocracia de falhar por causa de um espaço extra ou uma aspa simples.

---

## 3. Comandos Rápidos

```bash
# Limpar e formatar tudo agora
uv run ruff check --fix . && uv run ruff format .

# Rodar apenas os testes rápidos (Unitários)
uv run pytest tests/unit
```
