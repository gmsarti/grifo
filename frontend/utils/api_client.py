import requests
import streamlit as st
from requests.exceptions import ConnectionError, Timeout

API_BASE = "http://localhost:8000"

_CONNECTION_ERROR = (
    503,
    {
        "detail": "Não foi possível conectar à API. Certifique-se de que o servidor está rodando em localhost:8000."
    },
)


def api_is_ready() -> bool:
    """Retorna True se a API responder no endpoint /health."""
    try:
        r = requests.get(f"{API_BASE}/api/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except (ConnectionError, Timeout):
        return _CONNECTION_ERROR


# ---------- Auth ----------


def register(email: str, password: str, full_name: str | None = None):
    def _do():
        r = requests.post(
            f"{API_BASE}/api/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        return r.status_code, r.json()

    return _call(_do)


def login(email: str, password: str):
    def _do():
        r = requests.post(
            f"{API_BASE}/api/auth/token",
            data={"username": email, "password": password},
        )
        return r.status_code, r.json()

    return _call(_do)


# ---------- Projects ----------


def list_projects():
    def _do():
        r = requests.get(f"{API_BASE}/api/projects/", headers=_headers())
        return r.status_code, r.json()

    return _call(_do)


def create_project(name: str, description: str | None, system_prompt: str | None):
    def _do():
        r = requests.post(
            f"{API_BASE}/api/projects/",
            headers=_headers(),
            json={
                "name": name,
                "description": description,
                "system_prompt": system_prompt,
            },
        )
        return r.status_code, r.json()

    return _call(_do)


def get_project(project_id: int):
    def _do():
        r = requests.get(f"{API_BASE}/api/projects/{project_id}", headers=_headers())
        return r.status_code, r.json()

    return _call(_do)


# ---------- Chat ----------


def send_message(
    message: str,
    project_id: str,
    thread_id: str,
    user_id: str = "default_user",
    mode: str = "reflexion",
    max_iterations: int = 2,
    web_search: bool = True,
):
    def _do():
        payload = {
            "message": message,
            "project_id": project_id,
            "thread_id": thread_id,
            "user_id": user_id,
            "config": {
                "mode": mode,
                "max_iterations": max_iterations,
                "web_search": web_search,
            },
        }
        r = requests.post(f"{API_BASE}/api/v1/chat", json=payload)
        return r.status_code, r.json()

    return _call(_do)


# ---------- Documents ----------


def list_documents(project_id: str = "default"):
    def _do():
        r = requests.get(
            f"{API_BASE}/api/v1/documents", params={"project_id": project_id}
        )
        return r.status_code, r.json()

    return _call(_do)


def ingest_file(file_bytes: bytes, filename: str):
    def _do():
        r = requests.post(
            f"{API_BASE}/api/v1/ingest/upload",
            files={"file": (filename, file_bytes)},
        )
        return r.status_code, r.json()

    return _call(_do)


def ingest_url(url: str):
    def _do():
        r = requests.post(f"{API_BASE}/api/v1/ingest/url", json={"url": url})
        return r.status_code, r.json()

    return _call(_do)


def delete_document(doc_id: str, project_id: str = "default"):
    def _do():
        r = requests.delete(
            f"{API_BASE}/api/v1/documents/{doc_id}",
            params={"project_id": project_id},
        )
        return r.status_code, r.json()

    return _call(_do)


# ---------- Memory ----------


def get_facts(thread_id: str, user_id: str = "default_user"):
    def _do():
        r = requests.get(
            f"{API_BASE}/api/v1/memory/{thread_id}/facts",
            params={"user_id": user_id},
        )
        return r.status_code, r.json()

    return _call(_do)


def clear_memory(
    thread_id: str, project_id: str = "default", user_id: str = "default_user"
):
    def _do():
        r = requests.delete(
            f"{API_BASE}/api/v1/memory/{thread_id}",
            params={"project_id": project_id, "user_id": user_id},
        )
        return r.status_code, r.json()

    return _call(_do)
