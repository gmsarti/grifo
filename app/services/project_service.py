from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def get_user_projects(self, user_id: int) -> list[Project]:
        return await self.project_repo.get_by_owner(user_id)

    async def ensure_default_project(self, user_id: int) -> Project:
        """
        Ensures the user has at least one project. Creates a 'Default Project' if none exist.
        """
        projects = await self.project_repo.get_by_owner(user_id)
        if projects:
            return projects[0]

        project_in = ProjectCreate(
            name="Default Project", description="Your first workspace", owner_id=user_id
        )
        return await self.project_repo.create(project_in)
