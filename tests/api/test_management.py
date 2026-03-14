import pytest
from fastapi.testclient import TestClient
from app.api.routes import app
import os

client = TestClient(app)

def test_document_listing_and_deletion():
    """Tests GET /documents and DELETE /documents/{doc_id}."""
    # 1. List for a specific project
    response = client.get("/api/v1/documents?project_id=rpg-project")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    
    # If we have documents from the re-ingestion, let's try to "delete" something that doesn't exist
    # or just check the list is working.
    
    # 2. Delete non-existent
    response = client.delete("/api/v1/documents/non-existent-file.pdf?project_id=test-project")
    assert response.status_code == 200 # Deletion usually succeeds even if 0 items matched in Chroma
    assert "removido" in response.json()["message"]

def test_memory_management():
    """Tests GET /memory/{thread_id}/facts and DELETE /memory/{thread_id}."""
    thread_id = "test-thread-123"
    
    # 1. Get facts (should be empty)
    response = client.get(f"/api/v1/memory/{thread_id}/facts")
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == thread_id
    assert "facts" in data
    
    # 2. Delete memory
    response = client.delete(f"/api/v1/memory/{thread_id}?project_id=test-project")
    assert response.status_code == 200
    assert "limpa" in response.json()["message"]

def test_delete_document_path_param():
    """Verify that :path param handles slashes correctly."""
    doc_id = "path/to/my/document.pdf"
    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert doc_id in response.json()["message"]
