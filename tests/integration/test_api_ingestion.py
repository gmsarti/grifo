import pytest
import shutil
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

@pytest.fixture
def test_app():
    """Fixture to provide a clean app with a temporary chroma directory."""
    # Create a temp directory for this test run
    temp_dir = tempfile.mkdtemp()
    os.environ["CHROMA_PERSIST_DIRECTORY"] = temp_dir
    
    # Import app here so it uses the new environment variable
    from app.api.routes import app
    client = TestClient(app)
    
    yield client
    
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

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
