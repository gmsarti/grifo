from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.web.deps import get_current_web_user
from app.core.db import get_db
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.services.rag_service import RAGService
from app.services.rag_service_facade import AgenticRAGController

router = APIRouter()
templates = Jinja2Templates(directory="app/adapters/web/templates")


def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    chat_repo = ChatRepository(db)
    rag_controller = AgenticRAGController()
    return RAGService(chat_repo, rag_controller)


@router.get("/chat/{session_id}", response_class=HTMLResponse)
async def get_chat_page(
    request: Request,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_web_user),
):
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session_by_id(session_id)
    if not session:
        # For demo purposes, if session doesn't exist, we might want to create one
        # but here we'll just show an empty state or handle normally
        pass

    messages = await chat_repo.get_history(session_id)

    return templates.TemplateResponse(
        "pages/chat.html",
        {
            "request": request,
            "session_id": session_id,
            "messages": messages,
            "current_user": current_user,
        },
    )


@router.post("/chat/{session_id}/message", response_class=HTMLResponse)
async def post_chat_message(
    request: Request,
    session_id: int,
    message: str = Form(...),
    rag_service: RAGService = Depends(get_rag_service),
    current_user: User = Depends(get_current_web_user),
):
    # 1. Process the message and get response
    # In a real HTMX flow, we might want to return the user message immediately
    # and then trigger the AI response. But for simplicity in this task,
    # we'll do the sync-wait for now or use HX-Trigger.

    response_text = await rag_service.chat(session_id, message)

    # We return the AI message partial
    return templates.TemplateResponse(
        "partials/message.html",
        {"request": request, "role": "assistant", "content": response_text},
    )


@router.get("/chat/{session_id}/thinking", response_class=HTMLResponse)
async def get_thinking(request: Request):
    return templates.TemplateResponse("partials/thinking.html", {"request": request})
