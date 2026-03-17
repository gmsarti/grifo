from fastapi import APIRouter

from app.adapters.web.routes import auth, chat

router = APIRouter()

router.include_router(auth.router, tags=["auth"])
router.include_router(chat.router, tags=["chat"])
