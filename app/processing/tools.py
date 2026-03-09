from langchain.tools import tool
from app.data_source.vector_store import VectorStoreManager
from app.data_source.mcp_client import MCPConnector

# Instanciamos os conectores da Camada de Dados
vector_db = VectorStoreManager()
mcp_client = MCPConnector()


@tool
def get_company_knowledge(query: str) -> str:
    """
    Útil para procurar informações em documentos internos, manuais e base de conhecimento da empresa.
    Introduza a sua pergunta como texto (query).
    """
    return vector_db.search_context(query)


@tool
def check_external_system(action: str, details: str) -> str:
    """
    Útil para consultar sistemas externos via MCP (ex: verificar estado de servidores, consultar tickets).
    """
    return mcp_client.execute_action(action, {"details": details})


# Lista de ferramentas que o Agente terá à sua disposição
AGENT_TOOLS = [get_company_knowledge, check_external_system]
