import pytest


@pytest.fixture
async def auth_token(client):
    """
    Returns an auth token for a registered user.
    """
    email = "project_api@example.com"
    password = "password123"
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "API User"},
    )
    response = await client.post(
        "/api/auth/token", data={"username": email, "password": password}
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_project_api(client, auth_token):
    """
    Test project creation via API.
    """
    response = await client.post(
        "/api/projects/",
        json={"name": "New Project", "description": "Desc"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects_api(client, auth_token):
    """
    Test listing projects via API.
    """
    # Create one
    await client.post(
        "/api/projects/",
        json={"name": "Project Alpha"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    response = await client.get(
        "/api/projects/", headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(p["name"] == "Project Alpha" for p in data)


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    response = await client.get("/api/projects/")
    assert response.status_code == 401
