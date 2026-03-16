from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.token import Token
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService, create_access_token

router = APIRouter()


@router.post(
    "/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    # Check if user exists
    user = await user_repo.get_by_email(user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="User already exists")

    # In a real app, hash password here or in service.
    # Our service currently assumes hashed_password mapping.
    # We'll use service to hash.
    from app.services.auth_service import get_password_hash

    user_in.password = get_password_hash(user_in.password)

    return await user_repo.create(user_in)


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    user = await auth_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
