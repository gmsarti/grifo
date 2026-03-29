from pydantic import BaseModel, ConfigDict, field_validator

MAX_SYSTEM_PROMPT_LENGTH = 2000


class ProjectBase(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    owner_id: int | None = None
    is_active: bool | None = True

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v: str | None) -> str | None:
        if v is not None and len(v) > MAX_SYSTEM_PROMPT_LENGTH:
            raise ValueError(
                f"system_prompt não pode exceder {MAX_SYSTEM_PROMPT_LENGTH} caracteres "
                f"(recebido: {len(v)})"
            )
        return v


class ProjectCreate(ProjectBase):
    name: str


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)
