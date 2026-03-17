from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    owner_id: int | None = None
    is_active: bool | None = True


class ProjectCreate(ProjectBase):
    name: str


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)
