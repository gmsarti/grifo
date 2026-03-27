from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, Request

from app.adapters.web.deps import get_current_web_user, get_optional_current_web_user
from app.core.security import create_access_token


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.cookies = {}
    return request


async def test_get_optional_user_returns_none_without_cookie(mock_request, mock_db):
    user = await get_optional_current_web_user(mock_request, mock_db)
    assert user is None


async def test_get_optional_user_returns_user_with_valid_cookie(mock_request, mock_db):
    from unittest.mock import patch

    email = "a@b.com"
    token = create_access_token({"sub": email})
    mock_request.cookies = {"access_token": token}

    mock_user = MagicMock(email=email)

    with patch("app.adapters.web.deps.UserRepository") as MockRepo:
        repo_instance = MockRepo.return_value
        repo_instance.get_by_email = AsyncMock(return_value=mock_user)

        user = await get_optional_current_web_user(mock_request, mock_db)

        assert user == mock_user
        MockRepo.assert_called_once_with(mock_db)
        repo_instance.get_by_email.assert_called_once_with(email)


async def test_get_optional_user_returns_none_with_invalid_token(mock_request, mock_db):
    mock_request.cookies = {"access_token": "invalid-token"}
    user = await get_optional_current_web_user(mock_request, mock_db)
    assert user is None


async def test_get_current_web_user_returns_user_if_present():
    mock_user = MagicMock()
    user = await get_current_web_user(mock_user)
    assert user == mock_user


async def test_get_current_web_user_raises_redirect_if_none():
    with pytest.raises(HTTPException) as excinfo:
        await get_current_web_user(None)

    assert excinfo.value.status_code == 303
    assert excinfo.value.headers["Location"] == "/web/login"
