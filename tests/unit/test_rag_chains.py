from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.processing.rag.chains import (
    GradeDocuments,
    get_question_rewriter,
    get_rag_generation_chain,
    get_retrieval_grader,
)


def test_retrieval_grader():
    """Test the retrieval grader chain."""
    mock_llm = MagicMock()

    # Define a simple function that behaves like the structured LLM
    def structured_invoke(input):
        # input is a ChatPromptValue
        prompt_text = str(input)
        if "Grifo" in prompt_text:
            return GradeDocuments(binary_score="yes")
        return GradeDocuments(binary_score="no")

    with patch("app.processing.rag.chains.get_fast_model", return_value=mock_llm):
        mock_llm.with_structured_output.return_value = RunnableLambda(structured_invoke)

        grader = get_retrieval_grader()

        # Test relevant document
        res_yes = grader.invoke(
            {
                "question": "O que é o Grifo?",
                "document": "Grifo é um framework de agentes inteligentes.",
            }
        )
        assert res_yes.binary_score == "yes"

        # Test irrelevant document
        res_no = grader.invoke(
            {
                "question": "Qual a cor do céu?",
                "document": "O preço da maçã subiu ontem.",
            }
        )
        assert res_no.binary_score == "no"


def test_rag_generation_chain():
    """Test the RAG generation chain."""
    mock_llm = RunnableLambda(lambda x: AIMessage(content="Mocked answer"))
    with patch("app.processing.rag.chains.get_reasoner", return_value=mock_llm):
        chain = get_rag_generation_chain()

        context = "Grifo é um sistema de automação. Ele usa LangGraph."
        question = "O que é o Grifo?"

        res = chain.invoke({"context": context, "question": question})
        assert res.content == "Mocked answer"


def test_question_rewriter():
    """Test the question rewriter chain."""
    mock_llm = RunnableLambda(lambda x: AIMessage(content="Improved question"))
    with patch("app.processing.rag.chains.get_fast_model", return_value=mock_llm):
        rewriter = get_question_rewriter()

        question = "Como funciona o RAG no Grifo?"
        res = rewriter.invoke({"question": question})

        assert res.content == "Improved question"
