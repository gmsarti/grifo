# Guia de Estilo: Modern Scriptorium

Este documento documenta a identidade visual e as diretrizes de interface do projeto **Grifo**, garantindo consistência em futuras expansões.

## 1. A Direção Estética
A estética "Modern Scriptorium" busca transformar a ferramenta em um ambiente de concentração profunda, remetendo a uma biblioteca acadêmica clássica sob uma ótica moderna e tátil.

### Elementos Chave:
- **Papel e Textura**: Nada de fundos chapados. O uso de `grain-overlay` e texturas de papel é obrigatório.
- **Marginalia**: Citações e referências não devem poluir o fluxo principal; elas aparecem em uma calha lateral (como notas de rodapé).
- **Contraste Suave**: Uso de tons terrosos para reduzir a fadiga ocular.

---

## 2. Paleta de Cores (The Earth Spectrum)

Utilizamos variáveis CSS para manter a consistência.

| Nome | Hex | Uso |
| :--- | :--- | :--- |
| **Parchment** | `#F9F7F2` | Fundo principal da página |
| **Coffee** | `#2C1E1A` | Texto primário, bordas e ícones |
| **Terracotta** | `#A34E39` | Ações principais, links e indicadores ativos |
| **Sage** | `#6B705C` | Elementos secundários, estados de conclusão |

---

## 3. Tipografia

A tipografia é o que confere autoridade ao sistema.

| Uso | Fonte (Google Fonts) | Estilo |
| :--- | :--- | :--- |
| **Títulos / Display** | `Fraunces` | Soft Serif, Impressão vintage |
| **Corpo do Texto** | `Lora` | Serif contemporânea, leitura longa |
| **Metadados / UI** | `Space Mono` | Mono-espaçada, estética de arquivo/técnica |

---

## 4. Layout e Grid
A composição deve evitar a simetria centralizada tradicional de chatbots.

- **Proporção**: 60% para o conteúdo principal (Chat/Texto) e 40% para a **Marginalia** (Referências).
- **Divisores**: Linhas finas de `0.5px` com opacidade reduzida (`coffee/10` ou `coffee/20`).

---

## 5. Componentes e Classes CSS

Todas as classes estão definidas em `app/adapters/web/static/css/style.css`.

### Texturas
- `.grain-overlay`: Overlay fixo com 4-6% de opacidade para simular o grão do papel.

### Cartões e Bordas
- `.scriptorium-card`: Fundo parchment, borda sutil e sombra profunda mas suave.
- `radius`: Mantenha cantos vivos ou com arredondamento mínimo (`2px`).

### Animações (Motion)
- **Staggered Reveal**: As respostas da IA devem usar a classe `.staggered-reveal`. O texto não deve apenas aparecer; ele deve sofrer um fade-in com deslocamento vertical de `10px` e um leve desfoque inicial.

---

## 6. Diretrizes de Contraste (Refined)
Para garantir a legibilidade em fundos claros:
- **Texto de Metadados**: Mínimo de `60%` de opacidade (`text-coffee/60`).
- **Labels de Categoria**: Mínimo de `80%` de opacidade (`text-coffee/80`).
- **Citações na Marginalia**: Use itálico com `70%` de opacidade.

---

## 7. Referência de Implementação (Tailwind)

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        parchment: '#F9F7F2',
        coffee: '#2C1E1A',
        terracotta: '#A34E39',
        sage: '#6B705C',
      },
      fontFamily: {
        fraunces: ['Fraunces', 'serif'],
        lora: ['Lora', 'serif'],
        mono: ['Space Mono', 'monospace'],
      },
    }
  }
}
```
