from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
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
        self.executor = self._create_agent_executor()

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

    def _create_agent_executor(self):
        """Cria o agente LangChain capaz de chamar ferramentas."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "És um assistente corporativo inteligente. Utiliza as tuas ferramentas para procurar informação antes de responder.",
                ),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    async def process_message(self, message: str) -> str:
        """Processa a mensagem do utilizador e devolve a resposta do agente."""
        try:
            result = await self.executor.ainvoke({"input": message})
            return result["output"]
        except Exception as e:
            return f"Ocorreu um erro ao processar o raciocínio: {str(e)}"
