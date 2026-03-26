import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import delete_document, ingest_file, ingest_url, list_documents

st.set_page_config(page_title="Documentos – Grifo", page_icon="📄", layout="wide")
st.title("📄 Documentos")

if not st.session_state.get("token"):
    st.warning("Você precisa estar logado. Volte à página inicial.")
    st.stop()

if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = "default"

project_id = st.sidebar.text_input("Project ID", key="active_project_id")

# ---------- Listar documentos ----------
st.subheader("Documentos ingeridos")

col_refresh, _ = st.columns([1, 5])
with col_refresh:
    refresh = st.button("🔄 Atualizar")

status, data = list_documents(project_id)
if status != 200:
    st.error("Erro ao buscar documentos.")
else:
    docs = data.get("documents", [])
    if not docs:
        st.info("Nenhum documento ingerido ainda.")
    else:
        for doc in docs:
            col_doc, col_del = st.columns([5, 1])
            col_doc.markdown(f"📎 `{doc}`")
            if col_del.button("🗑️", key=f"del_{doc}", help="Remover"):
                s, r = delete_document(doc, project_id)
                if s == 200:
                    st.success(r.get("message", "Removido."))
                    st.rerun()
                else:
                    st.error(r.get("detail", "Erro ao remover."))

# ---------- Upload de arquivo ----------
st.divider()
st.subheader("Ingerir arquivo")

uploaded = st.file_uploader("Selecione um arquivo")
if st.button("Enviar arquivo") and uploaded:
    with st.spinner("Ingerindo…"):
        status, data = ingest_file(uploaded.read(), uploaded.name)
    if status == 200:
        st.success(f"Arquivo **{data['filename']}** ingerido com sucesso!")
        st.rerun()
    else:
        st.error(data.get("detail", "Erro ao ingerir arquivo."))

# ---------- Ingestão por URL ----------
st.divider()
st.subheader("Ingerir URL")

with st.form("ingest_url_form"):
    url = st.text_input("URL", placeholder="https://exemplo.com/documento")
    url_submitted = st.form_submit_button("Ingerir URL")

if url_submitted:
    if not url:
        st.error("Informe uma URL.")
    else:
        with st.spinner("Ingerindo…"):
            status, data = ingest_url(url)
        if status == 200:
            st.success(f"URL **{data['url']}** ingerida com sucesso!")
            st.rerun()
        else:
            st.error(data.get("detail", "Erro ao ingerir URL."))
