import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import clear_memory, get_facts

st.set_page_config(page_title="Memória – Grifo", page_icon="🧠", layout="wide")
st.title("🧠 Memória")

if not st.session_state.get("token"):
    st.warning("Você precisa estar logado. Volte à página inicial.")
    st.stop()

# Garante que as chaves compartilhadas existem
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = "default"
if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = "default_user"
if "chat_thread_id" not in st.session_state:
    st.session_state.chat_thread_id = ""

with st.sidebar:
    # Pré-preenche com os valores ativos da sessão
    thread_id = st.text_input(
        "Thread ID",
        value=st.session_state.get("chat_thread_id", ""),
        placeholder="Cole o ID da thread…",
    )
    project_id = st.text_input("Project ID", key="active_project_id")
    user_id = st.text_input("User ID", key="active_user_id")

if not thread_id:
    st.info("Informe um Thread ID no painel lateral para visualizar a memória.")
    st.stop()

# ---------- Fatos ----------
st.subheader(f"Fatos da thread `{thread_id}`")

if st.button("🔄 Atualizar"):
    st.rerun()

status, data = get_facts(thread_id, user_id)
if status != 200:
    st.error("Erro ao buscar fatos.")
else:
    facts = data.get("facts", [])
    if not facts:
        st.info("Nenhum fato registrado para esta thread.")
    else:
        for f in facts:
            if isinstance(f, dict):
                fact_text = f.get("fact", str(f))
                # O fato já inclui o tópico no formato "[Tópico] texto"
                if fact_text.startswith("[") and "]" in fact_text:
                    topic = fact_text[1 : fact_text.index("]")]
                    fact_body = fact_text[fact_text.index("]") + 2 :]
                else:
                    topic = "—"
                    fact_body = fact_text
            else:
                topic = "—"
                fact_body = str(f)
            with st.container(border=True):
                st.markdown(f"**Tópico:** {topic}")
                st.markdown(fact_body)

# ---------- Limpar memória ----------
st.divider()
st.subheader("Limpar memória")
st.warning(
    "Esta ação apaga o histórico de mensagens e todos os fatos da thread. Não pode ser desfeita."
)

if st.button("🗑️ Limpar memória desta thread", type="primary"):
    status, data = clear_memory(thread_id, project_id, user_id)
    if status == 200:
        st.success(data.get("message", "Memória limpa."))
    else:
        st.error(data.get("detail", "Erro ao limpar memória."))
