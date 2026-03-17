from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def register(self, email: str, full_name: str, password: str) -> User:
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("Email já cadastrado")

        return await self.user_repo.create_with_hash(email, full_name, password)
