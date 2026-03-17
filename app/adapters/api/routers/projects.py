from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.api import deps
from app.core.db import get_db
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import Project, ProjectCreate
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/", response_model=list[Project])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project_repo = ProjectRepository(db)
    project_service = ProjectService(project_repo)
    return await project_service.get_user_projects(current_user.id)


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # Ignore any owner_id sent by the client and force it to current_user.id
    obj_data = project_in.model_dump()
    obj_data["owner_id"] = current_user.id

    from app.models.project import Project as ProjectModel

    db_obj = ProjectModel(**obj_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
