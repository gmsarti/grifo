from langchain.tools import tool
from app.data_source.vector_store import VectorStoreManager
from app.data_source.mcp_client import MCPConnector
from app.processing.rag.controller import AgenticRAGController
import asyncio

# Instanciamos os conectores da Camada de Dados e Controladores
vector_db = VectorStoreManager()
mcp_client = MCPConnector()
rag_controller = AgenticRAGController()


@tool
def get_company_knowledge(query: str) -> str:
    """
    Útil para procurar informações em documentos internos, manuais e base de conhecimento da empresa.
    Esta ferramenta utiliza Corrective RAG (CRAG) com validação de documentos e busca web como fallback.
    Introduza a sua pergunta como texto (query).
    """
    # Como o controlador é assíncrono e a ferramenta espera síncrono (ou o LangChain gerencia):
    # Usamos asyncio.run para simplificar a ponte se necessário, 
    # ou deixamos o LangChain lidar com a corotina se registrado corretamente.
    return asyncio.run(rag_controller.invoke(query))


@tool
def check_external_system(action: str, details: str) -> str:
    """
    Útil para consultar sistemas externos via MCP (ex: verificar estado de servidores, consultar tickets).
    """
    return mcp_client.execute_action(action, {"details": details})


# Lista de ferramentas que o Agente terá à sua disposição
AGENT_TOOLS = [get_company_knowledge, check_external_system]
