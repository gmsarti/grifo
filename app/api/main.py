from fastapi import FastAPI

from app.api.routers import auth, projects

app = FastAPI(title="Agent Stack API")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])


@app.get("/")
async def root():
    return {"message": "Welcome to Agent Stack API"}
