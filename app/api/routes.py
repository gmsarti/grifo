from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.processing.agent import AgentOrchestrator

# Inicializamos o FastAPI
app = FastAPI(title="Agente Grifo", version="0.1.0")

# Instância única do orquestrador do agente
agent_orchestrator = AgentOrchestrator()


# Modelos Pydantic para os Endpoints
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


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
