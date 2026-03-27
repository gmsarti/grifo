import pytest


@pytest.fixture
async def auth_token(client):
    """Registra um usuário e retorna seu access token para testes de API autenticados."""
    email = "integration_user@example.com"
    password = "password123"
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Integration User"},
    )
    response = await client.post(
        "/api/auth/token", data={"username": email, "password": password}
    )
    return response.json()["access_token"]
