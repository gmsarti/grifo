import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.data_source.vector_store import VectorStoreManager
from app.processing.agent import AgentOrchestrator
from app.repositories.project_repository import ProjectRepository

logger = get_logger(__name__)

router = APIRouter()

# Singletons — garante que o InMemoryStore e o MemorySaver persistam entre requests
_orchestrator: AgentOrchestrator | None = None
_vector_store: VectorStoreManager | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Gets or creates the global AgentOrchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


async def reset_orchestrator():
    """Closes and resets the global orchestrator (useful for tests and lifespan)."""
    global _orchestrator
    if _orchestrator:
        try:
            await _orchestrator.close()
        except Exception:
            pass
        _orchestrator = None


def get_vector_store() -> VectorStoreManager:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store


# Modelos Pydantic para os Endpoints
class ChatConfig(BaseModel):
    mode: str = "reflexion"
    max_iterations: int = 2
    web_search: bool = True


class ChatRequest(BaseModel):
    message: str
    project_id: str
    thread_id: str
    user_id: str | None = "default_user"
    config: ChatConfig | None = ChatConfig()


class GroundingMetadata(BaseModel):
    local_sources: list[str] = []
    web_sources: list[str] = []
    search_queries: list[str] = []


class UsageInfo(BaseModel):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    latency_ms: float = 0


class ChatResponse(BaseModel):
    response: str
    project_id: str
    thread_id: str
    iterations: int
    grounding_metadata: GroundingMetadata
    process_trace: list[str]
    usage: UsageInfo


class UrlRequest(BaseModel):
    url: str


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_CHAT)
async def chat_endpoint(
    request: Request,
    body: ChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
):
    # Busca o system_prompt do projeto, se project_id for numérico
    system_prompt: str | None = None
    try:
        project_id_int = int(body.project_id)
        project_repo = ProjectRepository(db)
        project = await project_repo.get_by_id(project_id_int)
        if project:
            system_prompt = project.system_prompt or None
    except (ValueError, TypeError):
        pass  # project_id não numérico (ex: "default") — sem system_prompt

    try:
        result = await orchestrator.process_message(
            message=body.message,
            thread_id=body.thread_id,
            project_id=body.project_id,
            user_id=body.user_id,
            system_prompt=system_prompt,
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return ChatResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/upload")
async def upload_file(
    file: UploadFile = File(...),
    vector_store: VectorStoreManager = Depends(get_vector_store),
):
    temp_dir = Path("/tmp/grifo_ingestion")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        vector_store.ingest_file(str(temp_path))

        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.post("/ingest/url")
async def ingest_url(
    request: UrlRequest, vector_store: VectorStoreManager = Depends(get_vector_store)
):
    try:
        vector_store.ingest_url(request.url)
        return {"status": "success", "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    project_id: str | None = "default",
    vector_store: VectorStoreManager = Depends(get_vector_store),
):
    try:
        manager = vector_store
        if project_id != vector_store.project_id:
            manager = VectorStoreManager(project_id=project_id)

        docs = manager.list_documents()
        return {"status": "success", "documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id:path}")
async def delete_document(
    doc_id: str,
    project_id: str = "default",
    vector_store: VectorStoreManager = Depends(get_vector_store),
):
    try:
        manager = vector_store
        if project_id != vector_store.project_id:
            manager = VectorStoreManager(project_id=project_id)

        manager.delete_document(doc_id)
        return {"status": "success", "message": f"Documento {doc_id} removido."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{thread_id}/facts")
async def get_thread_facts(
    thread_id: str,
    user_id: str = "default_user",
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
):
    try:
        await orchestrator._ensure_initialized()
        facts = await orchestrator.store_manager.list_facts(user_id, thread_id)
        return {"status": "success", "thread_id": thread_id, "facts": facts}
    except Exception as e:
        logger.exception("Error in get_thread_facts")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{thread_id}")
async def delete_thread_memory(
    thread_id: str,
    project_id: str = "default",
    user_id: str = "default_user",
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
):
    try:
        await orchestrator._ensure_initialized()
        from app.processing.memory import VectorizedMessageHistory

        history = VectorizedMessageHistory(project_id, thread_id)
        history.delete_history()

        await orchestrator.store_manager.delete_thread_memory(user_id, thread_id)

        return {"status": "success", "message": f"Memória da thread {thread_id} limpa."}
    except Exception as e:
        logger.exception("Error in delete_thread_memory")
        raise HTTPException(status_code=500, detail=str(e))
