import datetime

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.schemas.agent_schemas import AnswerQuestion, KnowledgeExtraction, ReviseAnswer

# from langchain_core.messages import ToolCallRequest


def get_time():
    """Returns the current UTC time in ISO format."""
    return datetime.datetime.now(datetime.UTC).isoformat()


# Base template for all actor activities
actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert researcher and research assistant.
Current time: {time}

If there is memory context at the beginning of the conversation (labeled "Context from memory"), \
use it to adapt your response to the researcher's profile and background:
- Adjust depth and terminology to their expertise level
- Tailor the angle and focus to their research interests and trajectory
- Generate search queries that target aspects most relevant to their background and knowledge gaps

1. {first_instruction}
2. Reflect and critique your answer. Be severe to maximize improvement.
3. Recommend search queries tailored to the researcher's profile and the gaps identified in your critique.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
).partial(time=get_time)

# Specific Instructions
DRAFT_INSTRUCTION = "Provide a detailed ~250 word answer."
REVISE_INSTRUCTION = """Revise your previous answer using the new information.
- Use the previous critique to improve and deepen the answer
- Remove superfluous information identified in the critique
- Adapt the depth, terminology, and angle to the researcher's background and expertise \
(use any profile context available in memory)
- Ensure search queries target the most relevant aspects for this specific researcher's trajectory"""


def get_first_responder(llm):
    """
    Creates the first responder chain.
    Binds the AnswerQuestion tool to the LLM.
    """
    prompt = actor_prompt_template.partial(first_instruction=DRAFT_INSTRUCTION)

    return prompt | llm.bind_tools(
        tools=[AnswerQuestion],
        tool_choice={"type": "function", "function": {"name": "AnswerQuestion"}},
    )


def get_revisor(llm):
    """
    Creates the revisor chain.
    Binds the ReviseAnswer tool to the LLM.
    """
    prompt = actor_prompt_template.partial(first_instruction=REVISE_INSTRUCTION)
    return prompt | llm.bind_tools(
        tools=[ReviseAnswer],
        tool_choice={"type": "function", "function": {"name": "ReviseAnswer"}},
    )


def get_knowledge_extractor(llm):
    """
    Cria a chain responsável por extrair aprendizados da conversa.
    Utiliza structured output para garantir o formato da resposta.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Você é um especialista em extrair conhecimento útil de conversas para armazenar na memória de longo prazo.

Analise o histórico recente e extraia apenas informações que o usuário declarou ou demonstrou diretamente. Extraia qualquer um dos seguintes tipos:

- Preferências e características que o usuário afirmou explicitamente (tom, idioma, nível técnico)
- Contexto de trabalho ou projetos que o usuário mencionou
- Tópicos de interesse ou áreas de pesquisa que o usuário disse estar explorando
- Tecnologias ou ferramentas que o usuário declarou usar ou conhecer
- Fatos sobre a trajetória ou identidade do usuário que ele mesmo informou

REGRAS CRÍTICAS:
- Extraia somente o que o usuário disse diretamente. Não infira, não assuma, não especule.
- Se o usuário disse "uso Python", registre isso. Não adicione "pode estar interessado em Django".
- Um fato válido tem evidência textual clara na conversa. Se não houver, não extraia.
- Ignore saudações, perguntas triviais e qualquer informação que não seja uma declaração do próprio usuário.""",
            ),
            ("human", "Histórico da Conversa:\n{history}"),
        ]
    )

    structured_llm = llm.with_structured_output(KnowledgeExtraction)

    return prompt | structured_llm
