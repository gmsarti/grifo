# Pipeline de Extração de Padrões Arquitetônicos

Documenta como o sistema transforma linguagem natural em padrões arquitetônicos estruturados (a "linguagem intermediária"), usando como fio condutor o seguinte texto de exemplo:

> *"Quero projetar um quarto de casal. Nele deve haver uma cama de casal, dois criado mudo e um guarda-roupa. O guarda-roupa deve estar com as costas encostadas na parede. Cada criado mudo deve estar de um lado da cama e alinhados com a cabeceira."*

---

## Visão geral

```
┌──────────────────────────────┐     ┌────────────────────────────────────────┐
│      CAMINHO A — API         │     │       CAMINHO B — CHAT DO AGENTE       │
│  POST /api/v1/arq/extrair    │     │                                        │
│  { zona, mobiliario, texto } │     │  Usuário escreve mensagem em português │
└──────────────┬───────────────┘     └────────────────────┬───────────────────┘
               │                                          │
               │                              classify_node (router_chain.py)
               │                              ↳ detecta intent = "arq_extract"
               │                              ↳ extrai zona e mobiliário do texto
               │                                          │
               └──────────────────┬───────────────────────┘
                                  ▼
                     ArqService.extrair_padroes()
                     ┌─────────────────────────────────┐
                     │ 1. Valida zona + filtra catálogo │
                     │ 2. Monta lados alternativos      │
                     │ 3. Renderiza o prompt            │
                     │ 4. Invoca LLM (reasoner)         │
                     │ 5. Filtra erros → texto resumo   │
                     └───────────────┬─────────────────┘
                                     ▼
                         ExtrairPadroesResponse
                         { zona, mobiliario_valido,
                           padroes[], texto_resumo }
                                     │
               ┌─────────────────────┴─────────────────────┐
               │                                           │
        (Caminho A)                              (Caminho B)
        Retorna JSON ao                          Salva padrões na memória
        cliente HTTP                            de longo prazo do usuário
                                                + AIMessage ao chat
```

---

## Os dois caminhos de ativação

### Caminho A — API direta

**Endpoint:** `POST /api/v1/arq/extrair`
**Arquivo:** `app/adapters/api/routers/arq.py`

O caller já sabe o que quer e fornece tudo explicitamente no body:

```json
{
  "zona": "quarto",
  "mobiliario": ["cama", "criado-mudo", "guarda-roupa"],
  "texto": "O guarda-roupa deve estar com as costas encostadas na parede..."
}
```

Sem contexto de conversa. Os padrões extraídos **não** são salvos na memória do usuário.

### Caminho B — Chat do agente

O usuário envia uma mensagem em linguagem natural no chat. O agente executa dois nós do grafo LangGraph antes de chegar ao serviço:

**Nó 1 — `classify_node`** (`app/processing/agent.py:225`)
Usa o `router_chain` (modelo rápido) para classificar a mensagem:

```
intent:     "arq_extract"
zona:       "quarto"
mobiliario: ["cama", "criado-mudo", "guarda-roupa"]
```

O router recebe como contexto um resumo do vocabulário (apenas famílias de nível superior), o que guia o LLM a identificar nomes exatos em vez de variações livres.

**Roteamento** (`route_after_classify`):
Se `intent == "arq_extract"` **e** `zona` foi identificada → vai para `arq_extract_node`.
Sem zona → cai no fluxo reflexion (o agente pede mais contexto ao usuário).

**Nó 2 — `arq_extract_node`** (`app/processing/agent.py:263`)
- Se o router não identificou mobiliário específico, usa **todas as famílias da zona** como fallback
- Monta o `ExtrairPadroesRequest` e chama `arq_service.extrair_padroes()`
- Se padrões foram encontrados, salva na memória de longo prazo com UUID único
- Devolve o resultado como `AIMessage` com JSON formatado

---

## O vocabulário (`app/data/arq_vocabulary.py`)

Dados hardcoded que definem o que o sistema reconhece.

### Zonas válidas

```python
ZONAS = ["quarto", "sala", "cozinha", "banheiro"]
```

### Objetos por zona (estrutura hierárquica)

```python
OBJETOS_POR_ZONA["quarto"] = {
    "cama":        ["solteiro", "casal", "queen", "king"],  # família → folhas
    "guarda-roupa": ["2 portas", "3 portas"],
    "criado-mudo":  [],   # família sem variantes
    "escrivaninha": [],
}
```

O LLM pode referenciar um objeto como **família** (`{"nome": "cama"}`) ou como **folha** (`{"nome": "casal"}`), mas nunca pode inventar nomes. Termos não encontrados viram error-objects: `{"erro": "objeto_desconhecido", "texto": "termo usado"}`.

### Lados alternativos por objeto

```python
LADOS_POR_OBJETO = {
    "cama":          {"fundos": "cabeceira", "frente": "pés da cama"},
    "geladeira":     {"frente": "porta",     "fundos": "costas"},
    "sofa":          {"fundos": "encosto",   "frente": "assento"},
    "fogao":         {"frente": "frente da boca"},
    "vaso-sanitario":{"fundos": "cisterna"},
}
```

Os quatro lados canônicos são: `frente`, `fundos` (= `costas`), `lado direito`, `lado esquerdo`. Os apelidos acima são **exclusivos** de cada objeto — "cabeceira" só é válido para a cama. Se o usuário usar um apelido de lado de outro objeto, o LLM gera `{"erro": "lado_desconhecido", "texto": "termo usado"}`.

---

## O pipeline central (`app/services/arq_service.py`)

Cinco etapas executadas em sequência dentro de `ArqService.extrair_padroes()`:

### Etapa 1 — Validar zona e filtrar catálogo

Verifica se a zona existe em `ZONAS`. Então percorre `OBJETOS_POR_ZONA[zona]` e retém apenas os móveis solicitados (busca como chave de família, chave de subfamília ou folha). Móveis não encontrados na zona geram `HTTPException(422)`.

Para o exemplo, o catálogo filtrado é:

```json
{
  "cama":        ["solteiro", "casal", "queen", "king"],
  "criado-mudo": [],
  "guarda-roupa": ["2 portas", "3 portas"]
}
```

### Etapa 2 — Montar lados alternativos

`get_lados_for_objects(["cama", "criado-mudo", "guarda-roupa"])` retorna:

```json
[
  {"nome": "cama", "fundos": "cabeceira", "frente": "pés da cama"}
]
```

`criado-mudo` e `guarda-roupa` não têm aliases definidos, portanto não aparecem.

### Etapa 3 — Renderizar o prompt

`render_arq_prompt()` (`app/processing/arq_chain.py`) faz substituição direta (`str.replace`) de quatro variáveis no template `app/prompts/extrator_padroes_arq.md`:

| Variável   | Valor substituído                          |
|------------|--------------------------------------------|
| `$objetos` | dict de objetos filtrados (JSON indentado) |
| `$lados`   | lista de aliases de lados (JSON)           |
| `$zonas`   | `["quarto", "sala", "cozinha", "banheiro"]`|
| `$texto`   | texto original do usuário                  |

O resultado é um prompt completo com todas as instruções de gramática, exemplos e os dados concretos do contexto.

### Etapa 4 — Invocar o LLM (modelo reasoner)

`get_arq_extractor_chain()` usa `with_structured_output(PadroesExtraidos, method="function_calling")`. O **modelo reasoner** (maior capacidade) é usado porque a extração envolve gramática complexa com múltiplos padrões e referências cruzadas.

O LLM retorna um `PadroesExtraidos` com a lista de padrões extraídos — a **linguagem intermediária**.

### Etapa 5 — Filtrar erros e gerar texto resumo

`_strip_errors()` separa padrões válidos de error-objects. Erros são logados como warnings e não chegam ao cliente.

`padroes_para_texto()` (`app/processing/arq_text_converter.py`) converte cada padrão JSON em uma frase em português.

---

## A linguagem intermediária

Cada padrão extraído é um dict JSON com esta estrutura geral:

```json
{
  "tipo":   "restricao" | "preferencia" | "grid",
  "padrao": "<nome do padrão>",
  ... campos específicos do padrão ...
}
```

### Referência a objetos

| Caso | JSON |
|------|------|
| Família ou folha | `{"nome": "cama"}` |
| Família com exceção | `{"nome": "movel", "exceto": "sofa"}` |
| Múltiplos objetos distintos | `{"multiplo": [{"nome": "cama"}, {"nome": "sofa"}]}` |
| Objeto não reconhecido | `{"erro": "objeto_desconhecido", "texto": "termo usado"}` |

### Referência a lados

Usa o lado canônico (`frente`, `fundos`, `lado direito`, `lado esquerdo`). Se o apelido do usuário for inválido para aquele objeto: `{"erro": "lado_desconhecido", "texto": "termo usado"}`.

### Padrões suportados

**Tipo `restricao`:**

| Nome | Campos extras | Significado |
|------|---------------|-------------|
| `circulacao` | `objeto`, `gap` | Circulação mínima ao redor do objeto |
| `dentro_zona` | `objeto`, `zona` | Objeto deve estar em determinada zona |
| `dentro_objeto` | `objeto_pequeno`, `objeto_grande` | Um objeto sobre/dentro de outro |
| `encostado` | `objeto`, `lado` | Lado encostado na parede |
| `nao_encostado` | `objeto`, `lado` | Lado não encostado na parede |
| `distancia_maxima` | `objeto1`, `objeto2`, `gap` | Distância máxima entre dois objetos |
| `distancia_minima` | `objeto1`, `objeto2`, `gap` | Distância mínima entre dois objetos |
| `adjacente` | `objeto1`, `objeto2` | Objetos encostados um no outro |
| `virado_para_objeto` | `objeto1`, `lado`, `objeto2` | Lado virado para outro objeto |
| `paralelo` | `objeto` | Objeto(s) na mesma direção |
| `obstrucao` | `objeto1`, `lado`, `objeto2` | Deve haver obstrução entre lado e objeto |
| `nao_obstrucao` | `objeto1`, `lado`, `objeto2` | Não deve haver obstrução |
| `nao_sobreposicao_core` | `objeto` | Cores não se sobrepõem |
| `nao_sobreposicao_acesso` | `objeto` | Acessos não se sobrepõem |
| `nao_sobreposicao_par` | `objeto_core`, `objeto_acesso` | Core não sobrepõe acesso de outro |
| `projecao_ortogonal` | `objeto_sombra`, `objeto_sobreado`, `proporcao` | Projeção ortogonal mínima (%) |

**Tipo `preferencia`:**

| Nome | Campos extras |
|------|---------------|
| `preferencia_distancia_maxima` | `objeto1`, `objeto2`, `gap` |
| `preferencia_distancia_minima` | `objeto1`, `objeto2`, `gap` |
| `preferencia_projecao_ortogonal` | `objeto_sombra`, `objeto_sobreado`, `proporcao` |
| `preferencia_separacao_maxima` | `objeto1`, `objeto2` |
| `preferencia_escolha` | `objeto_preferencial`, `objeto_outro` |

**Tipo `grid`:**

| Nome | Campos extras |
|------|---------------|
| `grid_espaco` | `objeto`, `X`, `Y` |
| `grid_linha` | `objeto`, `X` |

---

## Exemplo completo

**Texto de entrada:**
> *"Quero projetar um quarto de casal. Nele deve haver uma cama de casal, dois criado mudo e um guarda-roupa. O guarda-roupa deve estar com as costas encostadas na parede. Cada criado mudo deve estar de um lado da cama e alinhados com a cabeceira."*

---

### Etapa 1 — Classificação (Caminho B)

O router detecta intent e contexto:

```
intent:     "arq_extract"
zona:       "quarto"          ← "quarto de casal"
mobiliario: ["cama",          ← "cama de casal"
             "criado-mudo",   ← "criado mudo"
             "guarda-roupa"]  ← "guarda-roupa"
```

---

### Etapa 2 — Catálogo filtrado para o prompt

```json
{
  "cama":        ["solteiro", "casal", "queen", "king"],
  "criado-mudo": [],
  "guarda-roupa": ["2 portas", "3 portas"]
}
```

---

### Etapa 3 — Lados alternativos para o prompt

```json
[
  {"nome": "cama", "fundos": "cabeceira", "frente": "pés da cama"}
]
```

O LLM recebe essa tabela e sabe que "cabeceira" é o apelido de `fundos` da cama. Para `criado-mudo` e `guarda-roupa` não há entradas, logo qualquer apelido de lado que não seja canônico geraria um `lado_desconhecido`.

---

### Etapa 4 — Linguagem intermediária (saída do LLM)

```json
[
  {
    "tipo": "restricao",
    "padrao": "encostado",
    "objeto": {"nome": "guarda-roupa"},
    "lado": "costas"
  },
  {
    "tipo": "restricao",
    "padrao": "adjacente",
    "objeto1": {"nome": "criado-mudo"},
    "objeto2": {"nome": "cama"}
  },
  {
    "tipo": "restricao",
    "padrao": "projecao_ortogonal",
    "objeto_sombra": {"nome": "criado-mudo"},
    "objeto_sobreado": {"nome": "cama"},
    "proporcao": 100
  }
]
```

**Decisões do LLM:**

- `"cama de casal"` → o LLM pode resolver como `{"nome": "casal"}` (folha, mais preciso) ou `{"nome": "cama"}` (família). Depende do quão específico for o padrão extraído.
- `"costas encostadas na parede"` → `lado: "costas"`, que é sinônimo de `fundos` (documentado no prompt como "fundos ou costas").
- `"de um lado da cama"` → padrão `adjacente` (um criado-mudo de cada lado). O LLM tipicamente gera dois padrões `adjacente` ou um único com objeto múltiplo.
- `"alinhados com a cabeceira"` → "cabeceira" é o alias de `fundos` da cama; alinhamento lateral vira `projecao_ortogonal` com proporção 100% (projeção total).

---

### Etapa 5 — Texto resumo

```
As costas de guarda-roupa deve estar encostado na parede.
criado-mudo deve estar encostado em cama.
criado-mudo deve ter uma projeção ortogonal de no mínimo 100% de cama.
```

---

## Arquivos-chave

| Arquivo | Responsabilidade | Input → Output |
|---------|-----------------|----------------|
| `app/adapters/api/routers/arq.py` | Endpoint HTTP | `ExtrairPadroesRequest` → `ExtrairPadroesResponse` |
| `app/processing/router_chain.py` | Classifica intenção e extrai zona/mobiliário | mensagem → `RouterDecision` |
| `app/processing/agent.py` | Nós `classify_node` e `arq_extract_node` do grafo | state → state atualizado |
| `app/services/arq_service.py` | Orquestra as 5 etapas do pipeline | `ExtrairPadroesRequest` → `ExtrairPadroesResponse` |
| `app/data/arq_vocabulary.py` | Vocabulário hardcoded | — (dados estáticos) |
| `app/processing/arq_chain.py` | Renderiza prompt + invoca LLM | `prompt_text` → `PadroesExtraidos` |
| `app/prompts/extrator_padroes_arq.md` | Template do prompt com gramática dos padrões | — (template) |
| `app/schemas/arq_schemas.py` | Schemas Pydantic: request, response, output do LLM | — (tipos) |
| `app/processing/arq_text_converter.py` | Converte padrões JSON em português | `list[dict]` → `str` |
