from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.adapters.api.main import router as api_router
from app.core.db import engine
from app.models.base import Base

app = FastAPI(title="Agent Stack")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # Import models here to ensure they are registered with Base.metadata
        from app import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


# Setup templates and static files
templates = Jinja2Templates(directory="app/adapters/web/templates")
app.mount("/static", StaticFiles(directory="app/adapters/web/static"), name="static")

# Include Adapters
app.include_router(api_router, prefix="/api")


@app.get("/web/", response_class=HTMLResponse)
async def web_root(request: Request):
    return templates.TemplateResponse(request, "base.html")


@app.get("/")
async def root():
    return {"message": "Welcome to Agent Stack - Use /api or /web/"}
