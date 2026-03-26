import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import send_message

st.set_page_config(page_title="Chat – Grifo", page_icon="💬", layout="wide")
st.title("💬 Chat")

if not st.session_state.get("token"):
    st.warning("Você precisa estar logado. Volte à página inicial.")
    st.stop()

# ---------- Estado da sessão ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
# Garante que as chaves compartilhadas existem (caso o usuário entre direto nesta página)
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = "default"
if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = "default_user"
if "chat_thread_id" not in st.session_state:
    st.session_state.chat_thread_id = str(uuid.uuid4())

# ---------- Configurações na sidebar ----------
with st.sidebar:
    st.header("Configurações")
    project_id = st.text_input("Project ID", key="active_project_id")
    user_id = st.text_input("User ID", key="active_user_id")
    mode = st.selectbox("Modo", ["reflexion", "simple"], index=0)
    max_iterations = st.slider("Máx. iterações", 1, 5, 2)
    web_search = st.checkbox("Busca web", value=True)

    st.divider()
    st.markdown(f"**Thread:** `{st.session_state.chat_thread_id}`")
    if st.button("🔄 Nova conversa"):
        st.session_state.chat_history = []
        st.session_state.chat_thread_id = str(uuid.uuid4())
        st.rerun()

# ---------- Histórico ----------
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("metadata"):
            meta = msg["metadata"]
            with st.expander("Detalhes da resposta"):
                if meta.get("process_trace"):
                    st.markdown("**Trace:**")
                    for step in meta["process_trace"]:
                        st.markdown(f"- {step}")
                grounding = meta.get("grounding_metadata", {})
                if grounding.get("web_sources"):
                    st.markdown("**Fontes web:**")
                    for s in grounding["web_sources"]:
                        st.markdown(f"- {s}")
                if grounding.get("local_sources"):
                    st.markdown("**Fontes locais:**")
                    for s in grounding["local_sources"]:
                        st.markdown(f"- {s}")
                usage = meta.get("usage", {})
                if usage:
                    cols = st.columns(3)
                    cols[0].metric("Tokens totais", usage.get("total_tokens", "—"))
                    cols[1].metric("Custo (USD)", f"${usage.get('total_cost', 0):.4f}")
                    cols[2].metric("Latência (ms)", f"{usage.get('latency_ms', 0):.0f}")

# ---------- Input ----------
user_input = st.chat_input("Digite sua mensagem…")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Pensando…"):
            status, data = send_message(
                message=user_input,
                project_id=project_id,
                thread_id=st.session_state.chat_thread_id,
                user_id=user_id,
                mode=mode,
                max_iterations=max_iterations,
                web_search=web_search,
            )

        if status == 200:
            response_text = data.get("response", "")
            st.markdown(response_text)
            metadata = {k: v for k, v in data.items() if k != "response"}
            with st.expander("Detalhes da resposta"):
                if data.get("process_trace"):
                    st.markdown("**Trace:**")
                    for step in data["process_trace"]:
                        st.markdown(f"- {step}")
                grounding = data.get("grounding_metadata", {})
                if grounding.get("web_sources"):
                    st.markdown("**Fontes web:**")
                    for s in grounding["web_sources"]:
                        st.markdown(f"- {s}")
                if grounding.get("local_sources"):
                    st.markdown("**Fontes locais:**")
                    for s in grounding["local_sources"]:
                        st.markdown(f"- {s}")
                usage = data.get("usage", {})
                if usage:
                    cols = st.columns(3)
                    cols[0].metric("Tokens totais", usage.get("total_tokens", "—"))
                    cols[1].metric("Custo (USD)", f"${usage.get('total_cost', 0):.4f}")
                    cols[2].metric("Latência (ms)", f"{usage.get('latency_ms', 0):.0f}")

            st.session_state.chat_history.append(
                {"role": "assistant", "content": response_text, "metadata": metadata}
            )
        else:
            error_msg = data.get("detail", "Erro ao processar mensagem.")
            st.error(error_msg)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": f"Erro: {error_msg}"}
            )
