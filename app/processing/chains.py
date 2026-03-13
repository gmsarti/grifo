import datetime
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.processing.schemas import AnswerQuestion, ReviseAnswer


def get_time():
    """Returns the current UTC time in ISO format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# Base template for all actor activities
actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are expert researcher.
Current time: {time}

1. {first_instruction}
2. Reflect and critique your answer. Be severe to maximize improvement.
3. Recommend search queries to research information and improve your answer.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
).partial(time=get_time)

# Specific Instructions
DRAFT_INSTRUCTION = "Provide a detailed ~250 word answer."
REVISE_INSTRUCTION = """Revise your previous answer using the new information.
- You should use the previous critique to improve the story
- You should use the previous critique to remove superfluous information
- You should use the previous critique to make the story more suitable to social context"""


def get_first_responder(llm):
    """
    Creates the first responder chain.
    Binds the AnswerQuestion tool to the LLM.
    """
    prompt = actor_prompt_template.partial(first_instruction=DRAFT_INSTRUCTION)
    return prompt | llm.bind_tools(tools=[AnswerQuestion], tool_choice="AnswerQuestion")


def get_revisor(llm):
    """
    Creates the revisor chain.
    Binds the ReviseAnswer tool to the LLM.
    """
    prompt = actor_prompt_template.partial(first_instruction=REVISE_INSTRUCTION)
    return prompt | llm.bind_tools(tools=[ReviseAnswer], tool_choice="ReviseAnswer")
