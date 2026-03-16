import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_get_projects_for_user():
    """
    Detailed:
    - Given a user_id
    - When service.get_user_projects is called
    - Then it should call repo.get_by_owner and return the list.
    """
    from app.services.project_service import ProjectService
    from app.models.project import Project

    mock_repo = MagicMock()
    mock_projects = [Project(id=1, name="P1"), Project(id=2, name="P2")]
    mock_repo.get_by_owner = AsyncMock(return_value=mock_projects)

    service = ProjectService(mock_repo)
    projects = await service.get_user_projects(user_id=1)

    assert projects == mock_projects
    mock_repo.get_by_owner.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_ensure_default_project_exists():
    """
    Test "Default Workspace" logic.
    - Given a user with NO projects
    - When service.ensure_default_project is called
    - Then it should create a new project named 'Default Project'.
    """
    from app.services.project_service import ProjectService
    from app.repositories.project_repository import ProjectRepository

    mock_repo = MagicMock(spec=ProjectRepository)
    mock_repo.get_by_owner = AsyncMock(return_value=[])
    mock_repo.create = AsyncMock(return_value=MagicMock(name="Default Project"))

    service = ProjectService(mock_repo)
    await service.ensure_default_project(user_id=1)

    # Verify creation
    mock_repo.create.assert_called_once()
    args, _ = mock_repo.create.call_args
    assert args[0].name == "Default Project"
    assert args[0].owner_id == 1


@pytest.mark.asyncio
async def test_ensure_default_project_already_exists():
    """
    - Given a user with existing projects
    - When service.ensure_default_project is called
    - Then it should NOT create a new one.
    """
    from app.services.project_service import ProjectService
    from app.models.project import Project

    mock_repo = MagicMock()
    mock_repo.get_by_owner = AsyncMock(return_value=[Project(id=1, name="Existing")])
    mock_repo.create = AsyncMock()

    service = ProjectService(mock_repo)
    await service.ensure_default_project(user_id=1)

    mock_repo.create.assert_not_called()
