import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import create_project, list_projects

st.set_page_config(page_title="Projetos – Grifo", page_icon="📁", layout="wide")
st.title("📁 Projetos")

if not st.session_state.get("token"):
    st.warning("Você precisa estar logado. Volte à página inicial.")
    st.stop()

# ---------- Listar projetos ----------
st.subheader("Seus projetos")

if st.button("🔄 Atualizar"):
    st.rerun()

status, data = list_projects()
if status != 200:
    st.error("Erro ao buscar projetos.")
else:
    projects = data
    if not projects:
        st.info("Nenhum projeto ainda. Crie um abaixo.")
    else:
        for p in projects:
            with st.expander(f"**{p['name']}** (id: {p['id']})"):
                st.markdown(f"**Descrição:** {p.get('description') or '—'}")
                st.markdown(f"**System prompt:** {p.get('system_prompt') or '—'}")
                st.markdown(f"**Ativo:** {'Sim' if p.get('is_active') else 'Não'}")

# ---------- Criar projeto ----------
st.divider()
st.subheader("Criar novo projeto")

with st.form("create_project_form"):
    name = st.text_input("Nome do projeto *")
    description = st.text_area("Descrição")
    system_prompt = st.text_area(
        "System prompt",
        placeholder="Instrução inicial para o agente neste projeto…",
    )
    submitted = st.form_submit_button("Criar")

if submitted:
    if not name:
        st.error("O nome é obrigatório.")
    else:
        status, data = create_project(name, description or None, system_prompt or None)
        if status == 201:
            st.success(f"Projeto **{data['name']}** criado com id `{data['id']}`!")
            st.rerun()
        else:
            st.error(data.get("detail", "Erro ao criar projeto."))
