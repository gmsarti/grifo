from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.adapters.api.main import router as api_router
from app.adapters.web.main import router as web_router
from app.core.db import engine
from app.core.rate_limit import limiter
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Import models here to ensure they are registered with Base.metadata
        from app import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    from app.adapters.api.routers.chat import reset_orchestrator

    await reset_orchestrator()


app = FastAPI(title="Agent Stack", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Setup templates and static files
templates = Jinja2Templates(directory="app/adapters/web/templates")
app.mount("/static", StaticFiles(directory="app/adapters/web/static"), name="static")

# Include Adapters
app.include_router(api_router, prefix="/api")
app.include_router(web_router, prefix="/web")


@app.get("/web/", response_class=HTMLResponse)
async def web_root(request: Request):
    return templates.TemplateResponse(request, "base.html")


@app.get("/")
async def root():
    return {"message": "Welcome to Agent Stack - Use /api or /web/"}
