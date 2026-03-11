import shutil
from pathlib import Path
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
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class UrlRequest(BaseModel):
    url: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal. A Interface do Utilizador (Streamlit) envia mensagens para aqui.
    """
    try:
        # A API atua como ponte, chamando o "Cérebro"
        answer = await agent_orchestrator.process_message(request.message)
        return ChatResponse(response=answer)
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
async def list_documents():
    """
    Retorna a lista de documentos (fontes) ingeridos no sistema.
    """
    try:
        docs = vector_store_manager.list_documents()
        return {"status": "success", "documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
