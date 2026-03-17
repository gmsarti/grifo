from unittest.mock import AsyncMock, MagicMock

import pytest

# from app.services.auth_service import AuthService
# from app.repositories.user_repository import UserRepository


@pytest.fixture
def mock_user_repo():
    return MagicMock()


@pytest.mark.asyncio
async def test_authenticate_user_success():
    """
    Test successful user authentication.
    - Given a user in DB
    - When authenticate is called with correct password
    - Then the user object should be returned.
    """
    from app.models.user import User
    from app.services.auth_service import AuthService

    # Setup mock
    repo = MagicMock()
    mock_user = User(email="test@example.com", hashed_password="hashed_password")
    repo.get_by_email = AsyncMock(return_value=mock_user)

    # Mock password verifying function (to be implemented)
    import app.services.auth_service as auth_module

    auth_module.verify_password = MagicMock(return_value=True)

    service = AuthService(repo)
    user = await service.authenticate("test@example.com", "password123")

    assert user == mock_user
    repo.get_by_email.assert_called_once_with("test@example.com")
    auth_module.verify_password.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password():
    """
    Test authentication failure due to wrong password.
    """
    from app.models.user import User
    from app.services.auth_service import AuthService

    repo = MagicMock()
    mock_user = User(email="test@example.com", hashed_password="hashed_password")
    repo.get_by_email = AsyncMock(return_value=mock_user)

    import app.services.auth_service as auth_module

    auth_module.verify_password = MagicMock(return_value=False)

    service = AuthService(repo)
    user = await service.authenticate("test@example.com", "wrongpass")

    assert user is None


@pytest.mark.asyncio
async def test_create_access_token():
    """
    Test JWT token generation.
    """
    from jose import jwt

    from app.services.auth_service import create_access_token

    data = {"sub": "test@example.com"}
    token = create_access_token(data)

    assert token is not None
    # Check if we can decode it (TDD: this will fail until jose is installed/used)
    from app.core.config import settings

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_creates_user(mock_user_repo):
    from app.services.auth_service import AuthService

    mock_user_repo.get_by_email = AsyncMock(return_value=None)
    mock_user_repo.create_with_hash = AsyncMock(return_value=MagicMock())

    service = AuthService(mock_user_repo)
    await service.register("a@b.com", "Ana", "senha123")

    mock_user_repo.get_by_email.assert_called_once_with("a@b.com")
    mock_user_repo.create_with_hash.assert_called_once_with(
        "a@b.com", "Ana", "senha123"
    )


@pytest.mark.asyncio
async def test_register_raises_if_email_exists(mock_user_repo):
    from app.services.auth_service import AuthService

    mock_user_repo.get_by_email = AsyncMock(
        return_value=MagicMock()
    )  # user already exists

    service = AuthService(mock_user_repo)
    with pytest.raises(ValueError, match="Email já cadastrado"):
        await service.register("a@b.com", "Ana", "senha123")
