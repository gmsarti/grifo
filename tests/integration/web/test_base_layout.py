from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_web_root_returns_base_template():
    """
    Test that the web root (which we'll define) returns a 200
    and contains the expected base HTML elements.
    """
    # This route hasn't been created yet, so it should fail (404)
    response = client.get("/web/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Grifo" in response.text


def test_static_files_accessible():
    """
    Test that static files are correctly mounted and accessible.
    """
    # This should fail until StaticFiles is mounted
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
