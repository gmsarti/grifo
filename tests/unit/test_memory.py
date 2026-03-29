import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore

from app.processing.memory import StoreMemoryManager, VectorizedMessageHistory


def _make_history(project_id="test_project", thread_id="test_thread"):
    with (
        patch("app.processing.memory.Chroma") as mock_chroma,
        patch("app.processing.memory.OpenAIEmbeddings"),
    ):
        history = VectorizedMessageHistory(project_id, thread_id)
        mock_vs = mock_chroma.return_value
        mock_vs.aadd_texts = AsyncMock()
        return history, mock_vs


async def test_add_message_usa_aadd_texts():
    thread_id = "test_thread_123"

    with (
        patch("app.processing.memory.Chroma") as mock_chroma,
        patch("app.processing.memory.OpenAIEmbeddings"),
    ):
        history = VectorizedMessageHistory("test_project", thread_id)
        mock_vs = mock_chroma.return_value
        mock_vs.aadd_texts = AsyncMock()

        await history.add_message(HumanMessage(content="Hello world"))

        mock_vs.aadd_texts.assert_awaited_once()


async def test_add_message_nao_usa_add_texts_sincrono():
    thread_id = "test_thread_456"

    with (
        patch("app.processing.memory.Chroma") as mock_chroma,
        patch("app.processing.memory.OpenAIEmbeddings"),
    ):
        history = VectorizedMessageHistory("test_project", thread_id)
        mock_vs = mock_chroma.return_value
        mock_vs.aadd_texts = AsyncMock()

        await history.add_message(HumanMessage(content="Hello world"))

        mock_vs.add_texts.assert_not_called()


async def test_add_message_duas_chamadas_simultaneas_nao_se_bloqueiam():
    with (
        patch("app.processing.memory.Chroma") as mock_chroma,
        patch("app.processing.memory.OpenAIEmbeddings"),
    ):
        history = VectorizedMessageHistory("test_project", "thread_concurrent")
        mock_vs = mock_chroma.return_value
        mock_vs.aadd_texts = AsyncMock()

        msg_a = HumanMessage(content="Mensagem A")
        msg_b = HumanMessage(content="Mensagem B")

        await asyncio.gather(
            history.add_message(msg_a),
            history.add_message(msg_b),
        )

        assert mock_vs.aadd_texts.await_count == 2


async def test_search_history_retorna_prefixo_correto():
    thread_id = "test_thread_search"

    with (
        patch("app.processing.memory.Chroma") as mock_chroma,
        patch("app.processing.memory.OpenAIEmbeddings"),
    ):
        history = VectorizedMessageHistory("test_project", thread_id)
        mock_vs = mock_chroma.return_value
        mock_vs.similarity_search.return_value = [
            MagicMock(page_content="Hello world", metadata={"type": "human"})
        ]

        res = history.search_history("hello")

        assert "User: Hello world" in res


# ── save_fact ────────────────────────────────────────────────────────────────


async def test_save_fact_uses_tuple_namespace():
    """save_fact deve passar namespace como tupla — list causa TypeError no InMemoryStore."""
    mock_store = AsyncMock(spec=InMemoryStore)
    manager = StoreMemoryManager(mock_store)

    await manager.save_fact("user1", "key1", "some fact")

    mock_store.aput.assert_called_once()
    _, kwargs = mock_store.aput.call_args
    assert isinstance(kwargs["namespace"], tuple), (
        "namespace deve ser tuple, não list; "
        "InMemoryStore.aput usa namespace como chave de dict e lança "
        "TypeError: unhashable type: 'list' com listas."
    )
    assert kwargs["namespace"] == ("memories", "user1")


async def test_save_fact_with_thread_id_uses_tuple_namespace():
    """Quando thread_id é fornecido, namespace ainda deve ser tuple."""
    mock_store = AsyncMock(spec=InMemoryStore)
    manager = StoreMemoryManager(mock_store)

    await manager.save_fact("user1", "key1", "some fact", thread_id="thread1")

    _, kwargs = mock_store.aput.call_args
    assert isinstance(kwargs["namespace"], tuple)
    assert kwargs["namespace"] == ("memories", "user1", "thread1")


async def test_save_fact_without_thread_id_excludes_thread_from_namespace():
    mock_store = AsyncMock(spec=InMemoryStore)
    manager = StoreMemoryManager(mock_store)

    await manager.save_fact("user1", "key1", "some fact", thread_id=None)

    _, kwargs = mock_store.aput.call_args
    assert kwargs["namespace"] == ("memories", "user1")
    assert len(kwargs["namespace"]) == 2


# ── search_memories ───────────────────────────────────────────────────────────


async def test_search_memories_uses_tuple_namespace():
    """search_memories deve passar namespace como tupla para asearch."""
    mock_store = AsyncMock(spec=InMemoryStore)
    mock_store.asearch = AsyncMock(return_value=[])
    manager = StoreMemoryManager(mock_store)

    await manager.search_memories("user1", "some query")

    mock_store.asearch.assert_called_once()
    call_args = mock_store.asearch.call_args
    # Primeiro argumento posicional é o namespace
    namespace = (
        call_args.args[0] if call_args.args else call_args.kwargs.get("namespace")
    )
    assert isinstance(namespace, tuple), (
        "asearch com namespace list retorna 0 resultados mesmo que existam fatos salvos."
    )
    assert namespace == ("memories", "user1")


async def test_search_memories_passes_query_and_limit():
    mock_store = AsyncMock(spec=InMemoryStore)
    mock_store.asearch = AsyncMock(return_value=[])
    manager = StoreMemoryManager(mock_store)

    await manager.search_memories("user1", "python frameworks", limit=3)

    call_args = mock_store.asearch.call_args
    assert call_args.kwargs.get("query") == "python frameworks" or (
        len(call_args.args) > 1 and call_args.args[1] == "python frameworks"
    )
    assert call_args.kwargs.get("limit") == 3


# ── integração com InMemoryStore real ────────────────────────────────────────


async def test_save_and_retrieve_with_real_store():
    """Com InMemoryStore real, fatos salvos devem ser encontrados por search_memories."""
    store = InMemoryStore()
    manager = StoreMemoryManager(store)

    await manager.save_fact(
        "user_real", "fact_001", "User prefers Python", thread_id="t1"
    )
    await manager.save_fact(
        "user_real", "fact_002", "User works on ML projects", thread_id="t1"
    )

    results = await manager.search_memories("user_real", "programming language")

    assert len(results) > 0, (
        "Nenhum fato foi encontrado — provável bug de namespace (list vs tuple) em save_fact ou search_memories."
    )
    contents = {r.value["content"] for r in results}
    assert any("Python" in c for c in contents)


async def test_save_fact_not_visible_to_other_users():
    """Fatos de um usuário não devem aparecer na busca de outro."""
    store = InMemoryStore()
    manager = StoreMemoryManager(store)

    await manager.save_fact("user_a", "fact_001", "User A likes Go", thread_id="t1")

    results = await manager.search_memories("user_b", "programming language")
    assert len(results) == 0


async def test_list_facts_returns_saved_facts():
    """list_facts deve retornar todos os fatos salvos para o usuário/thread."""
    store = InMemoryStore()
    manager = StoreMemoryManager(store)

    await manager.save_fact("user2", "fact_a", "fact content A", thread_id="t1")
    await manager.save_fact("user2", "fact_b", "fact content B", thread_id="t1")

    facts = await manager.list_facts("user2", "t1")

    assert len(facts) == 2, (
        "list_facts não retornou os fatos salvos. "
        "Possível bug em asearch(query='') com namespace incorreto."
    )
    contents = {f["fact"] for f in facts}
    assert "fact content A" in contents
    assert "fact content B" in contents


async def test_list_facts_empty_when_no_facts():
    store = InMemoryStore()
    manager = StoreMemoryManager(store)

    facts = await manager.list_facts("user_empty", "t1")
    assert facts == []


async def test_delete_thread_memory_removes_facts():
    store = InMemoryStore()
    manager = StoreMemoryManager(store)

    await manager.save_fact("user3", "fact_x", "will be deleted", thread_id="t_del")
    await manager.delete_thread_memory("user3", "t_del")

    facts = await manager.list_facts("user3", "t_del")
    assert len(facts) == 0


# ── teste legado (mantido para compatibilidade) ───────────────────────────────


async def test_store_memory_manager():
    mock_store = AsyncMock(spec=InMemoryStore)
    manager = StoreMemoryManager(mock_store)

    # Test save_fact — verifica chamada ao store (namespace deve ser tuple)
    await manager.save_fact("user1", "pref", "likes coffee")
    mock_store.aput.assert_called_once()
    _, kwargs = mock_store.aput.call_args
    assert kwargs["namespace"] == ("memories", "user1")
    assert kwargs["key"] == "pref"
    assert kwargs["value"]["content"] == "likes coffee"

    # Test search_memories
    mock_store.asearch.return_value = [MagicMock(value={"content": "likes coffee"})]
    res = await manager.search_memories("user1", "coffee")
    assert len(res) == 1
    assert res[0].value["content"] == "likes coffee"
