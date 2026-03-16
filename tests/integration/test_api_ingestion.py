import pytest
import shutil
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import importlib


@pytest.fixture
def test_app(monkeypatch):
    """Fixture to provide a clean app with a temporary chroma directory."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", temp_dir)

    # Reload config to pick up new env var
    import app.core.config

    importlib.reload(app.core.config)

    # Reload the router module to ensure vector_store_manager uses new config
    import app.api.routers.chat

    importlib.reload(app.api.routers.chat)

    from app.api.routers.chat import app

    client = TestClient(app)

    yield client

    # Cleanup
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


def test_upload_file_endpoint(test_app, mocker):
    print("\nSTART: test_upload_file_endpoint")
    # Mock embeddings to avoid external calls and hangs
    mocker.patch(
        "langchain_openai.OpenAIEmbeddings.embed_documents", return_value=[[0.1] * 1536]
    )
    mocker.patch(
        "langchain_openai.OpenAIEmbeddings.embed_query", return_value=[0.1] * 1536
    )

    client = test_app
    test_file = Path("test_endpoint_upload.txt")
    test_file.write_text("Conteúdo de teste para upload via endpoint API.")

    try:
        print("POSTing to /api/v1/ingest/upload")
        with test_file.open("rb") as f:
            response = client.post(
                "/api/v1/ingest/upload",
                files={"file": (test_file.name, f, "text/plain")},
            )
        print(f"RESPONSE STATUS: {response.status_code}")

        if response.status_code != 200:
            print(f"\nERROR DETAIL (upload): {response.text}")

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["filename"] == test_file.name

    finally:
        if test_file.exists():
            test_file.unlink()
    print("END: test_upload_file_endpoint")


def test_ingest_url_endpoint(test_app, mocker):
    print("\nSTART: test_ingest_url_endpoint")
    client = test_app
    target_url = "https://example.com"

    # Mocking necessary parts for the integration test
    from langchain_core.documents import Document

    mocker.patch(
        "langchain_community.document_loaders.WebBaseLoader.load",
        return_value=[
            Document(page_content="Mocked content", metadata={"source": target_url})
        ],
    )

    # Mock embeddings
    mocker.patch(
        "langchain_openai.OpenAIEmbeddings.embed_documents", return_value=[[0.1] * 1536]
    )
    mocker.patch(
        "langchain_openai.OpenAIEmbeddings.embed_query", return_value=[0.1] * 1536
    )

    print("POSTing to /api/v1/ingest/url")
    response = client.post("/api/v1/ingest/url", json={"url": target_url})
    print(f"RESPONSE STATUS: {response.status_code}")

    if response.status_code != 200:
        print(f"\nERROR DETAIL (url): {response.text}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    print("END: test_ingest_url_endpoint")


def test_list_documents_endpoint(test_app, mocker):
    print("\nSTART: test_list_documents_endpoint")
    # Mock embeddings
    mocker.patch(
        "langchain_openai.OpenAIEmbeddings.embed_documents", return_value=[[0.1] * 1536]
    )
    mocker.patch(
        "langchain_openai.OpenAIEmbeddings.embed_query", return_value=[0.1] * 1536
    )

    client = test_app
    test_file = Path("test_list.txt")
    test_file.write_text("Conteúdo para teste de listagem.")

    try:
        # 1. Ingest
        print("POSTing (ingest) to /api/v1/ingest/upload")
        with test_file.open("rb") as f:
            up_res = client.post(
                "/api/v1/ingest/upload",
                files={"file": (test_file.name, f, "text/plain")},
            )
            if up_res.status_code != 200:
                print(f"\nERROR DETAIL (list-ingest): {up_res.text}")

        # 2. List
        print("GETting /api/v1/documents")
        response = client.get("/api/v1/documents")
        print(f"RESPONSE STATUS: {response.status_code}")
        if response.status_code != 200:
            print(f"\nERROR DETAIL (list-get): {response.text}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        sources = [d["source"] for d in data.get("documents", [])]
        print(f"\nDEBUG sources in list: {sources}")
        assert any(test_file.name in s for s in sources)

    finally:
        if test_file.exists():
            test_file.unlink()
    print("END: test_list_documents_endpoint")
