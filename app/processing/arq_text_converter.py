"""
Conversor de padrões arquitetônicos JSON para texto em português.

Transforma a lista de padrões retornada pela chain de extração em frases
naturais em português, adequadas para exibição ao usuário.
"""

from typing import Any


class PatternToText:
    """Converte padrões arquitetônicos JSON para texto em português."""

    def __init__(self):
        self._restricao_handlers = {
            "circulacao": self._circulacao,
            "dentro_zona": self._dentro_zona,
            "dentro_objeto": self._dentro_objeto,
            "encostado": self._encostado,
            "nao_encostado": self._nao_encostado,
            "distancia_maxima": self._distancia_maxima,
            "distancia_minima": self._distancia_minima,
            "adjacente": self._adjacente,
            "virado_para_objeto": self._virado_para_objeto,
            "paralelo": self._paralelo,
            "obstrucao": self._obstrucao,
            "nao_obstrucao": self._nao_obstrucao,
            "nao_sobreposicao_core": self._nao_sobreposicao_core,
            "nao_sobreposicao_acesso": self._nao_sobreposicao_acesso,
            "nao_sobreposicao_par": self._nao_sobreposicao_par,
            "projecao_ortogonal": self._projecao_ortogonal,
        }

        self._preferencia_handlers = {
            "preferencia_distancia_maxima": self._pref_distancia_maxima,
            "preferencia_distancia_minima": self._pref_distancia_minima,
            "preferencia_projecao_ortogonal": self._pref_projecao_ortogonal,
            "preferencia_separacao_maxima": self._pref_separacao_maxima,
            "preferencia_escolha": self._pref_escolha,
        }

        self._grid_handlers = {
            "grid_espaco": self._grid_espaco,
            "grid_linha": self._grid_linha,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_objeto_name(self, obj: Any) -> str:
        if isinstance(obj, dict):
            if "erro" in obj:
                return f"<{obj.get('texto', 'desconhecido')}>"
            nome = obj.get("nome", "<desconhecido>")
            if "exceto" in obj:
                return f"{nome} (exceto {obj['exceto']})"
            return nome
        return str(obj)

    def _format_multiplo(self, multiplo: list) -> str:
        nomes = [self._extract_objeto_name(obj) for obj in multiplo]
        if len(nomes) == 1:
            return nomes[0]
        if len(nomes) == 2:
            return f"{nomes[0]} e {nomes[1]}"
        return ", ".join(nomes[:-1]) + f" e {nomes[-1]}"

    def _extract_objeto_name_with_multiplo(self, obj: Any) -> str:
        if isinstance(obj, dict):
            if "multiplo" in obj:
                return self._format_multiplo(obj["multiplo"])
            if "erro" in obj:
                return f"<{obj.get('texto', 'desconhecido')}>"
            return obj.get("nome", "<desconhecido>")
        return str(obj)

    def _descrever_lado(self, lado: Any) -> str:
        if isinstance(lado, dict) and "erro" in lado:
            return f"<{lado.get('texto', 'lado desconhecido')}>"
        lados_desc = {
            "frente": "a frente",
            "fundos": "os fundos",
            "costas": "as costas",
            "lado direito": "o lado direito",
            "lado esquerdo": "o lado esquerdo",
        }
        return lados_desc.get(str(lado), str(lado))

    # ── Restrições ────────────────────────────────────────────────────────────

    def _circulacao(self, p: dict) -> str:
        obj = self._extract_objeto_name(p["objeto"])
        return f"Deve haver uma circulação de {p['gap']}cm ao redor de {obj}."

    def _dentro_zona(self, p: dict) -> str:
        obj = self._extract_objeto_name(p["objeto"])
        return f"{obj} deve estar na {p['zona']}."

    def _dentro_objeto(self, p: dict) -> str:
        pequeno = self._extract_objeto_name(p["objeto_pequeno"])
        grande = self._extract_objeto_name(p["objeto_grande"])
        return f"{pequeno} deve estar sobre ou dentro de {grande}."

    def _encostado(self, p: dict) -> str:
        obj = self._extract_objeto_name(p["objeto"])
        lado = self._descrever_lado(p.get("lado", "fundos"))
        return f"{lado.capitalize()} de {obj} deve estar encostado na parede."

    def _nao_encostado(self, p: dict) -> str:
        obj = self._extract_objeto_name(p["objeto"])
        lado = self._descrever_lado(p.get("lado", "fundos"))
        return f"{lado.capitalize()} de {obj} não deve estar encostado na parede."

    def _distancia_maxima(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"{obj1} deve estar a uma distância máxima de {p['gap']}cm de {obj2}."

    def _distancia_minima(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"{obj1} deve estar a uma distância mínima de {p['gap']}cm de {obj2}."

    def _adjacente(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"{obj1} deve estar encostado em {obj2}."

    def _virado_para_objeto(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        lado = self._descrever_lado(p.get("lado", "frente"))
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"{lado.capitalize()} de {obj1} deve estar virado para {obj2}."

    def _paralelo(self, p: dict) -> str:
        obj = self._extract_objeto_name_with_multiplo(p["objeto"])
        return f"{obj} devem estar na mesma direção."

    def _obstrucao(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        lado = self._descrever_lado(p.get("lado", "frente"))
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"Deve haver obstrução entre {lado} de {obj1} e {obj2}."

    def _nao_obstrucao(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        lado = self._descrever_lado(p.get("lado", "frente"))
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"Não deve haver obstrução entre {lado} de {obj1} e {obj2}."

    def _nao_sobreposicao_core(self, p: dict) -> str:
        obj = self._extract_objeto_name_with_multiplo(p["objeto"])
        return f"O core de {obj} não devem ter sobreposição."

    def _nao_sobreposicao_acesso(self, p: dict) -> str:
        obj = self._extract_objeto_name_with_multiplo(p["objeto"])
        return f"O acesso de {obj} não devem ter sobreposição."

    def _nao_sobreposicao_par(self, p: dict) -> str:
        obj_core = self._extract_objeto_name(p["objeto_core"])
        obj_acesso = self._extract_objeto_name(p["objeto_acesso"])
        return f"O core de {obj_core} não deve ter sobreposição com o acesso de {obj_acesso}."

    def _projecao_ortogonal(self, p: dict) -> str:
        sombra = self._extract_objeto_name(p["objeto_sombra"])
        sobreado = self._extract_objeto_name(p["objeto_sobreado"])
        return f"{sombra} deve ter uma projeção ortogonal de no mínimo {p['proporcao']}% de {sobreado}."

    # ── Preferências ──────────────────────────────────────────────────────────

    def _pref_distancia_maxima(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"Preferencialmente, {obj1} deve estar a uma distância máxima de {p['gap']}cm de {obj2}."

    def _pref_distancia_minima(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"Preferencialmente, {obj1} deve estar a uma distância mínima de {p['gap']}cm de {obj2}."

    def _pref_projecao_ortogonal(self, p: dict) -> str:
        sombra = self._extract_objeto_name(p["objeto_sombra"])
        sobreado = self._extract_objeto_name(p["objeto_sobreado"])
        return (
            f"Preferencialmente, {sombra} deve ter uma projeção ortogonal "
            f"de no mínimo {p['proporcao']}% de {sobreado}."
        )

    def _pref_separacao_maxima(self, p: dict) -> str:
        obj1 = self._extract_objeto_name(p["objeto1"])
        obj2 = self._extract_objeto_name(p["objeto2"])
        return f"Preferencialmente, {obj1} deve estar o mais longe possível de {obj2}."

    def _pref_escolha(self, p: dict) -> str:
        pref = self._extract_objeto_name(p["objeto_preferencial"])
        outro = self._extract_objeto_name(p["objeto_outro"])
        return f"Preferencialmente, escolha {pref} em vez de {outro}."

    # ── Grids ─────────────────────────────────────────────────────────────────

    def _grid_espaco(self, p: dict) -> str:
        obj = self._extract_objeto_name(p["objeto"])
        x = p["X"]
        y = p.get("Y", x)
        return f"{obj} pode estar em qualquer ponto de um reticulado de {x}cm por {y}cm."

    def _grid_linha(self, p: dict) -> str:
        obj = self._extract_objeto_name(p["objeto"])
        return f"{obj} pode estar em qualquer ponto da parede com passo de {p['X']}cm."

    # ── Conversão ─────────────────────────────────────────────────────────────

    def _processar_padrao(self, padrao: dict) -> str:
        tipo = padrao.get("tipo")
        nome = padrao.get("padrao")

        if tipo == "restricao":
            handler = self._restricao_handlers.get(nome)
        elif tipo == "preferencia":
            handler = self._preferencia_handlers.get(nome)
        elif tipo == "grid":
            handler = self._grid_handlers.get(nome)
        else:
            handler = None

        if handler:
            return handler(padrao)
        return f"[Padrão desconhecido: {tipo}/{nome}]"

    def converter(self, padroes: list[dict]) -> str:
        """
        Converte uma lista de padrões JSON em texto em português.

        Retorna "Nenhum padrão identificado." se a lista estiver vazia.
        Cada padrão vira uma frase; as frases são unidas por espaço.
        """
        if not padroes:
            return "Nenhum padrão identificado."
        frases = [self._processar_padrao(p) for p in padroes]
        return " ".join(frases)


def padroes_para_texto(padroes: list[dict]) -> str:
    """Converte uma lista de padrões arquitetônicos em texto em português."""
    return PatternToText().converter(padroes)


_TIPO_HEADERS = {
    "restricao": "Restrições",
    "preferencia": "Preferências",
    "grid": "Posicionamento em grid",
}


def padroes_para_markdown(
    padroes: list[dict],
    zona: str | None = None,
    mobiliario: list[str] | None = None,
) -> str:
    """
    Converte padrões arquitetônicos em Markdown legível para exibição no chat.

    Diferente de padroes_para_texto(), agrupa por tipo (restrições, preferências,
    grids) e formata como lista com bullets. Inclui cabeçalho de contexto se zona
    e mobiliário forem fornecidos.
    """
    converter = PatternToText()
    lines: list[str] = []

    if zona:
        mob_str = ", ".join(mobiliario) if mobiliario else "—"
        lines.append(f"**Padrões identificados — {zona}**")
        lines.append(f"Mobiliário: {mob_str}")
        lines.append("")

    # Filtra itens sem tipo (referências de objeto soltas que o LLM pode emitir)
    padroes_validos = [p for p in padroes if "tipo" in p and "padrao" in p]

    if not padroes_validos:
        lines.append("Nenhum padrão identificado.")
        return "\n".join(lines)

    # Agrupa preservando a ordem de aparição dos tipos
    grupos: dict[str, list[str]] = {}
    for p in padroes_validos:
        tipo = p.get("tipo", "")
        frase = converter._processar_padrao(p)
        grupos.setdefault(tipo, []).append(frase)

    for tipo, frases in grupos.items():
        header = _TIPO_HEADERS.get(tipo, tipo.capitalize())
        lines.append(f"**{header}**")
        for frase in frases:
            lines.append(f"- {frase}")
        lines.append("")

    return "\n".join(lines).rstrip()
