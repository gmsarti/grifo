from unittest.mock import AsyncMock, patch

from app.models.user import User


async def test_get_login_page(client):
    response = await client.get("/web/login")
    assert response.status_code == 200
    assert "Login" in response.text
    assert 'name="email"' in response.text
    assert 'name="password"' in response.text


async def test_get_register_page(client):
    response = await client.get("/web/register")
    assert response.status_code == 200
    assert "Cadastro" in response.text or "Register" in response.text
    assert 'name="full_name"' in response.text
    assert 'name="email"' in response.text


async def test_post_login_success(client):
    mock_user = User(email="a@b.com", full_name="Ana", hashed_password="hashed")

    with patch("app.adapters.web.routes.auth.AuthService") as MockService:
        service_instance = MockService.return_value
        service_instance.authenticate = AsyncMock(return_value=mock_user)

        with patch("app.adapters.web.routes.auth.create_access_token") as mock_token:
            mock_token.return_value = "fake-token"

            response = await client.post(
                "/web/login",
                data={"email": "a@b.com", "password": "password123"},
                follow_redirects=False,
            )

            assert response.status_code == 303
            assert response.headers["Location"] == "/web/chat/1"
            assert "access_token=fake-token" in response.headers["set-cookie"]


async def test_post_login_failure(client):
    with patch("app.adapters.web.routes.auth.AuthService") as MockService:
        service_instance = MockService.return_value
        service_instance.authenticate = AsyncMock(return_value=None)

        response = await client.post(
            "/web/login",
            data={"email": "a@b.com", "password": "wrong"},
        )

        assert response.status_code == 200
        assert "Email ou senha inválidos" in response.text


async def test_post_register_success(client):
    with patch("app.adapters.web.routes.auth.AuthService") as MockService:
        service_instance = MockService.return_value
        service_instance.register = AsyncMock()

        response = await client.post(
            "/web/register",
            data={
                "full_name": "Ana",
                "email": "a@b.com",
                "password": "pass",
                "password_confirm": "pass",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["Location"] == "/web/login?registered=true"
        service_instance.register.assert_called_once()


async def test_post_logout(client):
    response = await client.post("/web/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["Location"] == "/web/login"
    assert 'access_token="";' in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


async def test_chat_unauthenticated_redirect(client):
    # This assumes we have protected the route
    response = await client.get("/web/chat/1", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["Location"] == "/web/login"
