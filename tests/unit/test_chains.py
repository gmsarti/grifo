from unittest.mock import MagicMock

import pytest

from app.processing.chains import (
    DRAFT_INSTRUCTION,
    REVISE_INSTRUCTION,
    actor_prompt_template,
    get_first_responder,
    get_knowledge_extractor,
    get_revisor,
)
from app.schemas.agent_schemas import AnswerQuestion, KnowledgeExtraction, ReviseAnswer


def test_actor_prompt_template_partial():
    """Verifica que o placeholder {time} é substituído por um valor real no momento da invocação."""
    from app.processing.chains import actor_prompt_template

    prompt = actor_prompt_template.invoke({"messages": [], "first_instruction": "test"})
    system_msg = prompt.messages[0].content
    assert "Current time:" in system_msg
    assert "{time}" not in system_msg


def test_get_first_responder():
    mock_llm = MagicMock()
    chain = get_first_responder(mock_llm)

    # Verify chain structure (RunnableSequence or similar)
    # The chain is: prompt | llm.bind_tools(...)
    assert chain is not None

    # Verify LLM was called with bind_tools
    mock_llm.bind_tools.assert_called_once()
    args, kwargs = mock_llm.bind_tools.call_args
    assert AnswerQuestion in kwargs["tools"]
    assert kwargs["tool_choice"] == {
        "type": "function",
        "function": {"name": "AnswerQuestion"},
    }


def test_get_revisor():
    mock_llm = MagicMock()
    chain = get_revisor(mock_llm)

    assert chain is not None

    # Verify LLM was called with bind_tools
    mock_llm.bind_tools.assert_called_once()
    args, kwargs = mock_llm.bind_tools.call_args
    assert ReviseAnswer in kwargs["tools"]
    assert kwargs["tool_choice"] == {
        "type": "function",
        "function": {"name": "ReviseAnswer"},
    }


def test_chain_prompts():
    mock_llm = MagicMock()

    # Test first responder prompt injection
    first_resp = get_first_responder(mock_llm)
    # The partial values are stored in partial_variables
    assert first_resp.first.partial_variables["first_instruction"] == DRAFT_INSTRUCTION

    # Test revisor prompt injection
    revisor = get_revisor(mock_llm)
    assert revisor.first.partial_variables["first_instruction"] == REVISE_INSTRUCTION


# ── get_knowledge_extractor ───────────────────────────────────────────────────


def test_get_knowledge_extractor_returns_chain():
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    chain = get_knowledge_extractor(mock_llm)

    assert chain is not None
    mock_llm.with_structured_output.assert_called_once_with(KnowledgeExtraction)


@pytest.mark.prompt_contract
def test_knowledge_extractor_prompt_covers_research_topics():
    """
    O prompt deve cobrir tópicos de pesquisa e técnicos, não apenas preferências
    pessoais. Um prompt que só menciona 'preferências' fará o LLM retornar facts=[]
    para conversas de pesquisa/Q&A.
    """
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    get_knowledge_extractor(mock_llm)

    # Acessa o prompt da chain (primeiro elemento da sequência)
    # get_knowledge_extractor retorna: prompt | structured_llm
    # A chain é uma RunnableSequence; o primeiro step é o ChatPromptTemplate
    chain = get_knowledge_extractor(mock_llm)
    prompt_template = chain.first

    # Extrai o texto do system message do prompt
    system_message = prompt_template.messages[0]
    prompt_text = system_message.prompt.template.lower()

    # O prompt deve cobrir tanto pesquisa quanto preferências pessoais
    research_keywords = [
        "pesquisa",
        "interesse",
        "tópico",
        "tecnologia",
        "domínio",
        "conhecimento",
    ]
    personal_keywords = ["preferência", "usuário", "projeto"]

    has_research_coverage = any(kw in prompt_text for kw in research_keywords)
    has_personal_coverage = any(kw in prompt_text for kw in personal_keywords)

    assert has_research_coverage, (
        f"Prompt não cobre tópicos de pesquisa/técnicos. "
        f"Palavras esperadas (pelo menos uma): {research_keywords}. "
        f"Prompt atual: {prompt_text[:300]}"
    )
    assert has_personal_coverage, (
        f"Prompt não cobre preferências pessoais/projetos. "
        f"Palavras esperadas (pelo menos uma): {personal_keywords}."
    )


# ── actor_prompt_template — uso do perfil do pesquisador ─────────────────────


@pytest.mark.prompt_contract
def test_actor_prompt_instructs_use_of_researcher_profile():
    """
    O system prompt base deve instruir explicitamente o LLM a usar o contexto de
    memória do pesquisador para adaptar profundidade, terminologia e ângulo.
    Não basta que "researcher" apareça no papel do agente — o prompt precisa
    orientar o USO do perfil armazenado em memória.
    """
    system_message = actor_prompt_template.messages[0]
    prompt_text = system_message.prompt.template.lower()

    # Deve haver instrução explícita de adaptação ao perfil/background do pesquisador
    adaptation_phrases = [
        "researcher's profile",
        "researcher's background",
        "adapt",
        "expertise level",
        "memory context",
        "context from memory",
    ]
    has_explicit_adaptation = any(
        phrase in prompt_text for phrase in adaptation_phrases
    )

    assert has_explicit_adaptation, (
        "O actor_prompt_template não instrui explicitamente o LLM a usar o perfil "
        "do pesquisador vindo da memória. Não basta ter 'researcher' no papel — é "
        "preciso orientar o USO do contexto de memória para adaptar a resposta.\n"
        f"Frases esperadas (pelo menos uma): {adaptation_phrases}\n"
        f"Prompt atual:\n{system_message.prompt.template}"
    )


@pytest.mark.prompt_contract
def test_actor_prompt_instructs_tailored_search_queries():
    """
    O LLM deve ser instruído a adaptar as queries de busca ao perfil do pesquisador,
    não apenas gerar queries genéricas sobre o tópico.
    """
    system_message = actor_prompt_template.messages[0]
    prompt_text = system_message.prompt.template.lower()

    # Deve haver instrução sobre queries adaptadas ao pesquisador
    tailored_query_phrases = [
        "search queries tailored",
        "tailored to the researcher",
        "researcher's profile",
        "researcher's background",
        "knowledge gaps",
    ]
    has_tailored_queries = any(
        phrase in prompt_text for phrase in tailored_query_phrases
    )

    assert has_tailored_queries, (
        "O prompt não instrui o LLM a adaptar queries de busca ao perfil do pesquisador. "
        "Queries genéricas ignoram o background e o nível de expertise do usuário.\n"
        f"Frases esperadas (pelo menos uma): {tailored_query_phrases}\n"
        f"Prompt atual:\n{system_message.prompt.template}"
    )


@pytest.mark.prompt_contract
def test_revise_instruction_adapts_to_researcher_background():
    """
    REVISE_INSTRUCTION deve incluir instrução para adaptar a resposta revisada
    ao background e nível de expertise do pesquisador.
    """
    revise_text = REVISE_INSTRUCTION.lower()

    researcher_keywords = [
        "researcher",
        "background",
        "expertise",
        "profile",
        "perfil",
        "pesquisador",
        "trajetória",
        "nível",
        "conhecimento",
    ]
    has_researcher_adaptation = any(kw in revise_text for kw in researcher_keywords)

    assert has_researcher_adaptation, (
        "REVISE_INSTRUCTION não menciona adaptação ao perfil do pesquisador. "
        "A revisão não aproveitará os fatos conhecidos sobre quem faz a pesquisa.\n"
        f"Instrução atual:\n{REVISE_INSTRUCTION}"
    )


@pytest.mark.prompt_contract
def test_knowledge_extractor_schema_topic_covers_research():
    """
    O campo 'topic' de ExtractedFact deve guiar o LLM a classificar fatos de
    pesquisa (ex: 'Interesse de Pesquisa') além de preferências pessoais.
    """
    from app.schemas.agent_schemas import ExtractedFact

    topic_description = ExtractedFact.model_fields["topic"].description.lower()

    research_examples = [
        "pesquisa",
        "interesse",
        "tecnologia",
        "trabalho",
        "conhecimento",
    ]
    has_research_example = any(kw in topic_description for kw in research_examples)

    assert has_research_example, (
        f"Campo 'topic' de ExtractedFact não exemplifica categorias de pesquisa/técnico. "
        f"Descrição atual: '{topic_description}'"
    )


# ── anti-especulação: extração ancorada em declarações diretas ────────────────


@pytest.mark.prompt_contract
def test_knowledge_extractor_prompt_prohibits_speculation():
    """
    O prompt deve proibir explicitamente a inferência de fatos não declarados.
    Sem essa restrição, o LLM extrapola ("pode estar interessado em X", "poderia
    explorar Y") com base em suposições, não no que o usuário afirmou.
    """
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()
    chain = get_knowledge_extractor(mock_llm)
    prompt_text = chain.first.messages[0].prompt.template.lower()

    # O prompt deve conter instrução explícita contra inferência/especulação
    no_speculation_phrases = [
        "não infira",
        "não assuma",
        "não especule",
        "declarou",
        "afirmou",
        "explicitamente",
        "diretamente",
        "apenas o que",
        "somente o que",
    ]
    has_anti_speculation = any(
        phrase in prompt_text for phrase in no_speculation_phrases
    )

    assert has_anti_speculation, (
        "O prompt não proíbe especulação. O LLM vai extrapolar interesses e tecnologias "
        "não mencionadas pelo usuário (ex: 'pode estar interessado em DevOps' quando o "
        "usuário só disse que usa Python).\n"
        f"Frases esperadas (pelo menos uma): {no_speculation_phrases}\n"
        f"Prompt atual:\n{chain.first.messages[0].prompt.template}"
    )


@pytest.mark.prompt_contract
def test_extracted_fact_description_requires_direct_statement():
    """
    A descrição do campo 'fact' em ExtractedFact deve orientar o LLM a ancorar
    cada fato em algo que o usuário afirmou diretamente, impedindo suposições.
    """
    from app.schemas.agent_schemas import ExtractedFact

    fact_description = ExtractedFact.model_fields["fact"].description.lower()

    grounding_phrases = [
        "declarou",
        "afirmou",
        "mencionou",
        "disse",
        "explicitamente",
        "diretamente",
        "stated",
        "declared",
    ]
    has_grounding = any(phrase in fact_description for phrase in grounding_phrases)

    assert has_grounding, (
        "A descrição do campo 'fact' não orienta o LLM a ancorar o fato em "
        "declarações diretas do usuário. Isso permite que o LLM escreva fatos "
        "especulativos como 'Usuário pode estar interessado em X'.\n"
        f"Frases esperadas (pelo menos uma): {grounding_phrases}\n"
        f"Descrição atual: '{ExtractedFact.model_fields['fact'].description}'"
    )
