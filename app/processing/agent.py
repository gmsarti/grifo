from langchain_openai import ChatOpenAI
from langchain.agents import create_agent  # Nova importação
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.config import settings
from app.processing.tools import AGENT_TOOLS


class AgentOrchestrator:
    """
    Processing Layer: O "Cérebro" da aplicação.
    Orquestra o LLM e as ferramentas, independente da API ou da UI.
    """

    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = AGENT_TOOLS
        self.agent = self._create_agent()  # Atribui diretamente


    def _initialize_llm(self):
        """Inicializa o modelo baseando-se nas configurações (DeepSeek ou OpenAI)."""
        if settings.MODEL_PROVIDER == "deepseek":
            return ChatOpenAI(
                model=settings.MODEL_NAME,
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1",
                max_tokens=1024,
            )
        # Default para OpenAI
        return ChatOpenAI(
            model=settings.MODEL_NAME, api_key=settings.OPENAI_API_KEY, temperature=0.2
        )

    def _create_agent(self):
        """Cria o agente LangChain moderno com tool calling."""
        system_prompt = "És um assistente corporativo inteligente. Utiliza as tuas ferramentas para procurar informação antes de responder."

        # Cria agente diretamente (CompiledStateGraph)
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
        )
        return agent

    async def process_message(self, message: str) -> str:
        """Processa a mensagem do utilizador e devolve a resposta do agente."""
        try:
            # O CompiledStateGraph do create_agent espera um dicionário com 'messages'
            inputs = {"messages": [{"role": "user", "content": message}]}
            result = await self.agent.ainvoke(inputs)
            
            # O resultado costuma ser o estado final, pegamos a última mensagem
            if "messages" in result and len(result["messages"]) > 0:
                return result["messages"][-1].content
            return "Não foi possível gerar uma resposta."
        except Exception as e:
            return f"Ocorreu um erro ao processar o raciocínio: {str(e)}"
