import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def test_user(db_session: AsyncSession):
    from app.models.user import User

    email = f"user_{uuid.uuid4()}@example.com"
    user = User(
        email=email,
        hashed_password="hashed_password",
        full_name="Test Owner",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user):
    from app.models.project import Project

    project = Project(name="Test Project", owner_id=test_user.id)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project
