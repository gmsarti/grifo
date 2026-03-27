import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# These imports will fail initially (TDD Red Phase)
# from app.repositories.user_repository import UserRepository
# from app.schemas.user import UserCreate


async def test_create_user(db_session: AsyncSession):
    """
    Test individual user creation in the repository.
    Detailed:
    - Given a user payload
    - When repository.create is called
    - Then the user should be returned with an ID and persisted in DB.
    """
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserCreate

    repo = UserRepository(db_session)
    user_in = UserCreate(
        email="test@example.com", password="password123", full_name="Test User"
    )

    user = await repo.create(user_in)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"


async def test_get_user_by_email(db_session: AsyncSession):
    """
    Test retrieving a user by email.
    """
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserCreate

    repo = UserRepository(db_session)
    user_in = UserCreate(email="findme@example.com", password="password123")
    await repo.create(user_in)

    found_user = await repo.get_by_email("findme@example.com")
    assert found_user is not None
    assert found_user.email == "findme@example.com"


async def test_get_user_by_id(db_session: AsyncSession):
    """
    Test retrieving a user by ID.
    """
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserCreate

    repo = UserRepository(db_session)
    user_in = UserCreate(email="idtest@example.com", password="password123")
    created_user = await repo.create(user_in)

    found_user = await repo.get_by_id(created_user.id)
    assert found_user is not None
    assert found_user.id == created_user.id


async def test_duplicate_email_raises_error(db_session: AsyncSession):
    """
    Ensure that creating a user with an existing email fails.
    """

    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserCreate

    repo = UserRepository(db_session)
    user_in = UserCreate(email="duplicate@example.com", password="password123")
    await repo.create(user_in)

    with pytest.raises(
        Exception
    ):  # We expect some form of failure (IntegrityError or custom)
        await repo.create(user_in)


async def test_create_user_with_hash_stores_hashed_password(db_session: AsyncSession):
    """
    Test individual user creation in the repository using password hashing.
    """
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(db_session)
    user = await repo.create_with_hash("a@b.com", "Ana", "senha123")
    assert user.hashed_password != "senha123"
    assert user.email == "a@b.com"
    assert user.full_name == "Ana"
