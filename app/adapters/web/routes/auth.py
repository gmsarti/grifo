from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter()
templates = Jinja2Templates(directory="app/adapters/web/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, registered: bool = False):
    return templates.TemplateResponse(
        request, "pages/login.html", {"registered": registered}
    )


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    user = await auth_service.authenticate(email, password)
    if not user:
        return templates.TemplateResponse(
            request, "pages/login.html", {"error": "Email ou senha inválidos"}
        )

    token = create_access_token({"sub": user.email})
    response = RedirectResponse(url="/web/chat/1", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "pages/register.html")


@router.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if password != password_confirm:
        return templates.TemplateResponse(
            request, "pages/register.html", {"error": "Senhas não conferem"}
        )

    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    try:
        await auth_service.register(email, full_name, password)
        return RedirectResponse(url="/web/login?registered=true", status_code=303)
    except ValueError as e:
        return templates.TemplateResponse(
            request, "pages/register.html", {"error": str(e)}
        )


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/web/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response
