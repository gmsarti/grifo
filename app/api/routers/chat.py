import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.processing.agent import AgentOrchestrator
from app.data_source.vector_store import VectorStoreManager

# Inicializamos o FastAPI
app = FastAPI(title="Agente Grifo", version="0.1.0")

# Instâncias dos serviços
agent_orchestrator = AgentOrchestrator()
vector_store_manager = VectorStoreManager()


# Modelos Pydantic para os Endpoints
class ChatConfig(BaseModel):
    mode: str = "reflexion"
    max_iterations: int = 2
    web_search: bool = True

class ChatRequest(BaseModel):
    message: str
    project_id: str
    thread_id: str
    user_id: Optional[str] = "default_user"
    config: Optional[ChatConfig] = ChatConfig()

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


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal. Suporta fluxo de reflexão e busca híbrida.
    """
    try:
        # Passa os identificadores hierárquicos para o orquestrador
        result = await agent_orchestrator.process_message(
            message=request.message,
            thread_id=request.thread_id,
            project_id=request.project_id,
            user_id=request.user_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return ChatResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ingest/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Processa e armazena arquivos locais usando pathlib para gestão de diretórios.
    """
    temp_dir = Path("/tmp/grifo_ingestion")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # O VectorStoreManager agora recebe a string do caminho
        vector_store_manager.ingest_file(str(temp_path))
        
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/v1/ingest/url")
async def ingest_url(request: UrlRequest):
    """
    Processa e armazena conteúdo de uma URL.
    """
    try:
        vector_store_manager.ingest_url(request.url)
        return {"status": "success", "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/documents")
async def list_documents(project_id: Optional[str] = "default"):
    """
    Retorna a lista de documentos (fontes) ingeridos no sistema.
    Opcionalmente filtrado por projeto.
    """
    try:
        # Se o projeto for diferente do atual, criamos um manager temporário
        manager = vector_store_manager
        if project_id != vector_store_manager.project_id:
            manager = VectorStoreManager(project_id=project_id)
            
        docs = manager.list_documents()
        return {"status": "success", "documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/documents/{doc_id:path}")
async def delete_document(doc_id: str, project_id: str = "default"):
    """
    Remove um documento do Vector Store por ID (caminho/URL).
    """
    try:
        manager = VectorStoreManager(project_id=project_id)
        manager.delete_document(doc_id)
        return {"status": "success", "message": f"Documento {doc_id} removido."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/memory/{thread_id}/facts")
async def get_thread_facts(thread_id: str, user_id: str = "default_user"):
    """
    Recupera fatos e preferências da memória de longo prazo.
    """
    try:
        facts = await agent_orchestrator.store_manager.list_facts(user_id, thread_id)
        return {"status": "success", "thread_id": thread_id, "facts": facts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/memory/{thread_id}")
async def delete_thread_memory(
    thread_id: str, 
    project_id: str = "default", 
    user_id: str = "default_user"
):
    """
    Limpa o histórico de chat e os fatos da thread.
    """
    try:
        # 1. Limpa histórico vetorizado
        from app.processing.memory import VectorizedMessageHistory
        history = VectorizedMessageHistory(project_id, thread_id)
        history.delete_history()
        
        # 2. Limpa fatos no Store
        await agent_orchestrator.store_manager.delete_thread_memory(user_id, thread_id)
        
        return {"status": "success", "message": f"Memória da thread {thread_id} limpa."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
