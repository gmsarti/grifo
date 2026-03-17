from fastapi import APIRouter

from app.adapters.api.routers import auth, projects

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])


@router.get("/")
async def root():
    return {"message": "Welcome to Agent Stack API"}
