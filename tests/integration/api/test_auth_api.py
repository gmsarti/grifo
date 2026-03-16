import pytest


@pytest.mark.asyncio
async def test_register_user_integration(client):
    """
    Test user registration via API.
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "api_test@example.com",
            "password": "password123",
            "full_name": "API Test User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "api_test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_login_user_integration(client):
    """
    Test user login and token acquisition.
    """
    # First register
    await client.post(
        "/api/auth/register",
        json={"email": "login_test@example.com", "password": "password123"},
    )

    # Then login
    response = await client.post(
        "/api/auth/token",
        data={
            "username": "login_test@example.com",
            "password": "password123",
        },  # OAuth2 style
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/api/auth/token",
        data={"username": "notfound@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401
