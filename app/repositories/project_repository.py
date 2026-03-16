from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.project import Project
from app.repositories.user_repository import BaseRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_by_owner(self, owner_id: int) -> list[Project]:
        result = await self.db.execute(
            select(self.model).filter(self.model.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def update(self, id: int, obj_in: ProjectUpdate) -> Project | None:
        db_obj = await self.get_by_id(id)
        if db_obj:
            update_data = obj_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj
