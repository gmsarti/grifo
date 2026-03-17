from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


async def get_optional_current_web_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    return user


async def get_current_web_user(
    user: User | None = Depends(get_optional_current_web_user),
) -> User:
    if not user:
        raise HTTPException(
            status_code=303,
            detail="Não autenticado",
            headers={"Location": "/web/login"},
        )
    return user
