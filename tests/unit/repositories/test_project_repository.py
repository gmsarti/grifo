import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# These will fail initially (Red Phase)
# from app.repositories.project_repository import ProjectRepository
# from app.schemas.project import ProjectCreate
# from app.models.user import User


@pytest.fixture
async def test_user(db_session: AsyncSession, request):
    import uuid

    from app.models.user import User

    email = f"owner_{uuid.uuid4()}@example.com"
    user = User(
        email=email,
        hashed_password="hashed_password",
        full_name="Owner",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession, test_user):
    """
    Test individual project creation in the repository.
    Detailed:
    - Given a project payload with a valid owner_id
    - When repository.create is called
    - Then the project should be returned with an ID and persisted.
    """
    from app.repositories.project_repository import ProjectRepository
    from app.schemas.project import ProjectCreate

    repo = ProjectRepository(db_session)
    project_in = ProjectCreate(
        name="Test Project", description="A test project", owner_id=test_user.id
    )

    project = await repo.create(project_in)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.owner_id == test_user.id


@pytest.mark.asyncio
async def test_get_projects_by_owner(db_session: AsyncSession, test_user):
    """
    Test retrieving all projects for a specific owner.
    """
    from app.repositories.project_repository import ProjectRepository
    from app.schemas.project import ProjectCreate

    repo = ProjectRepository(db_session)
    await repo.create(ProjectCreate(name="P1", owner_id=test_user.id))
    await repo.create(ProjectCreate(name="P2", owner_id=test_user.id))

    projects = await repo.get_by_owner(test_user.id)
    assert len(projects) >= 2
    assert any(p.name == "P1" for p in projects)
    assert any(p.name == "P2" for p in projects)


@pytest.mark.asyncio
async def test_update_project(db_session: AsyncSession, test_user):
    """
    Test updating project metadada/system prompt.
    """
    from app.repositories.project_repository import ProjectRepository
    from app.schemas.project import ProjectCreate, ProjectUpdate

    repo = ProjectRepository(db_session)
    created = await repo.create(ProjectCreate(name="Original", owner_id=test_user.id))

    update_data = ProjectUpdate(name="Updated", system_prompt="Be helpful")
    updated = await repo.update(created.id, update_data)

    assert updated.name == "Updated"
    assert updated.system_prompt == "Be helpful"
