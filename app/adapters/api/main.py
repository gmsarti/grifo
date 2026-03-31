from fastapi import APIRouter

from app.adapters.api.routers import arq, auth, chat, projects

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(chat.router, prefix="/v1", tags=["chat"])
router.include_router(arq.router, prefix="/v1/arq", tags=["arq"])


@router.get("/")
async def root():
    return {"message": "Welcome to Agent Stack API"}


@router.get("/health")
async def health():
    return {"status": "ok"}
