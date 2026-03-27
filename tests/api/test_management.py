async def test_document_listing_and_deletion(client):
    """Tests GET /documents and DELETE /documents/{doc_id}."""
    response = await client.get("/api/v1/documents?project_id=rpg-project")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data

    response = await client.delete(
        "/api/v1/documents/non-existent-file.pdf?project_id=test-project"
    )
    assert response.status_code == 200
    assert "removido" in response.json()["message"]


async def test_memory_management(client):
    """Tests GET /memory/{thread_id}/facts and DELETE /memory/{thread_id}."""
    thread_id = "test-thread-123"

    response = await client.get(f"/api/v1/memory/{thread_id}/facts")
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == thread_id
    assert "facts" in data

    response = await client.delete(
        f"/api/v1/memory/{thread_id}?project_id=test-project"
    )
    assert response.status_code == 200
    assert "limpa" in response.json()["message"]


async def test_delete_document_path_param(client):
    """Verify that :path param handles slashes correctly."""
    doc_id = "path/to/my/document.pdf"
    response = await client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert doc_id in response.json()["message"]
