import pytest
import shutil
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

@pytest.fixture
def test_app():
    """Fixture to provide a clean app with a temporary chroma directory."""
    import importlib
    import sys
    import app.core.config
    import app.api.routes
    
    # Create a temp directory for this test run
    temp_dir = tempfile.mkdtemp()
    os.environ["CHROMA_PERSIST_DIRECTORY"] = temp_dir
    
    # Force reload of settings and routes to pick up the new env var
    importlib.reload(app.core.config)
    importlib.reload(app.api.routes)
    
    from app.api.routes import app
    client = TestClient(app)
    
    yield client
    
    # Cleanup after test
    if os.path.exists(temp_dir):
        # We might need to safely close connections if Chroma allowed it, 
        # but for now we just try to rmtree.
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass # Ignore cleanup errors in tests if files are locked

def test_upload_file_endpoint(test_app):
    client = test_app
    # Create a dummy file
    test_file = Path("test_endpoint_upload.txt")
    test_file.write_text("Conteúdo de teste para upload via endpoint API.")
    
    try:
        with test_file.open("rb") as f:
            response = client.post(
                "/api/v1/ingest/upload",
                files={"file": (test_file.name, f, "text/plain")}
            )
        
        if response.status_code != 200:
            print(f"Error Response: {response.json()}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["filename"] == test_file.name
        
    finally:
        if test_file.exists():
            test_file.unlink()

def test_ingest_url_endpoint(test_app, mocker):
    client = test_app
    target_url = "https://example.com"
    
    # Mock the WebBaseLoader.load method to return a dummy document
    from langchain_core.documents import Document
    mock_load = mocker.patch("langchain_community.document_loaders.WebBaseLoader.load")
    mock_load.return_value = [Document(page_content="Mocked web content", metadata={"source": target_url})]
    
    response = client.post(
        "/api/v1/ingest/url",
        json={"url": target_url}
    )
    
    if response.status_code != 200:
        print(f"Error Response: {response.json()}")
        
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["url"] == target_url
    assert mock_load.called

def test_list_documents_endpoint(test_app):
    client = test_app
    # 1. Ingest a file
    test_file = Path("test_list.txt")
    test_file.write_text("Conteúdo para teste de listagem.")
    try:
        with test_file.open("rb") as f:
            client.post("/api/v1/ingest/upload", files={"file": (test_file.name, f, "text/plain")})
        
        # 2. Call the list endpoint
        response = client.get("/api/v1/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Check if our file is in the list
        sources = [d["source"] for d in data["documents"]]
        assert any(test_file.name in s for s in sources)
        
    finally:
        if test_file.exists():
            test_file.unlink()
