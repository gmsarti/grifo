from fastapi import APIRouter

from app.adapters.web.routes import chat

router = APIRouter()

router.include_router(chat.router, tags=["chat"])
