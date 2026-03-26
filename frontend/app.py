import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from utils.api_client import api_is_ready, login, register

st.set_page_config(page_title="Grifo", page_icon="🦅", layout="centered")

st.title("🦅 Grifo")
st.caption("Assistente de IA com memória e busca")

if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
# Configurações compartilhadas entre páginas
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = "default"
if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = "default_user"
if "chat_thread_id" not in st.session_state:
    import uuid

    st.session_state.chat_thread_id = str(uuid.uuid4())

# ---------- Status da API ----------
with st.sidebar:
    if api_is_ready():
        st.success("API online", icon="🟢")
    else:
        st.error("API offline", icon="🔴")
        st.caption("Aguardando localhost:8000…")
        if st.button("🔄 Verificar novamente"):
            st.rerun()

# ---------- Conteúdo principal ----------
if st.session_state.token:
    st.success(f"Logado como **{st.session_state.user_email}**")
    if st.button("Sair"):
        st.session_state.token = None
        st.session_state.user_email = None
        st.rerun()
    st.info(
        "Use o menu lateral para navegar entre Chat, Projetos, Documentos e Memória."
    )
else:
    if not api_is_ready():
        st.warning(
            "A API ainda não está disponível. Aguarde o servidor inicializar e clique em **Verificar novamente** no painel lateral."
        )
        st.stop()

    tab_login, tab_register = st.tabs(["Entrar", "Cadastrar"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
        if submitted:
            if not email or not password:
                st.error("Preencha todos os campos.")
            else:
                status, data = login(email, password)
                if status == 200:
                    st.session_state.token = data["access_token"]
                    st.session_state.user_email = email
                    st.success("Login realizado!")
                    st.rerun()
                else:
                    st.error(data.get("detail", "Falha no login."))

    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input("Nome completo (opcional)")
            reg_email = st.text_input("E-mail")
            reg_password = st.text_input("Senha", type="password")
            reg_submitted = st.form_submit_button("Cadastrar")
        if reg_submitted:
            if not reg_email or not reg_password:
                st.error("Preencha e-mail e senha.")
            else:
                status, data = register(reg_email, reg_password, full_name or None)
                if status == 201:
                    st.success("Conta criada! Faça login para continuar.")
                else:
                    st.error(data.get("detail", "Falha no cadastro."))
