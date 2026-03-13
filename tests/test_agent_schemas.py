from app.processing.schemas import Reflection, AnswerQuestion, ReviseAnswer
import pytest
from pydantic import ValidationError


def test_reflection_schema():
    reflection = Reflection(missing="missing info", superfluous="extra info")
    assert reflection.missing == "missing info"
    assert reflection.superfluous == "extra info"


def test_answer_question_schema():
    reflection = Reflection(missing="missing info", superfluous="extra info")
    answer = AnswerQuestion(
        answer="This is a 250 word answer...",
        reflection=reflection,
        search_queries=["query 1", "query 2"],
    )
    assert answer.answer == "This is a 250 word answer..."
    assert answer.reflection.missing == "missing info"
    assert len(answer.search_queries) == 2


def test_revise_answer_schema():
    reflection = Reflection(missing="missing info", superfluous="extra info")
    revised = ReviseAnswer(
        answer="Revised answer...",
        reflection=reflection,
        search_queries=["new query"],
        references=["source 1", "source 2"],
    )
    assert revised.answer == "Revised answer..."
    assert revised.references == ["source 1", "source 2"]


def test_invalid_schemas():
    with pytest.raises(ValidationError):
        # Missing required field
        Reflection(missing="only missing")

    with pytest.raises(ValidationError):
        # Invalid type for search_queries
        AnswerQuestion(
            answer="answer",
            reflection=Reflection(missing="m", superfluous="s"),
            search_queries="not a list",
        )
