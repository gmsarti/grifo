"""
Testes de integração para B-002: persistência da memória de longo prazo entre restarts.

Critério de aceite:
- Fatos salvos numa sessão persistem após restart do servidor.
- Testes verificam persistência entre instâncias distintas do AgentOrchestrator.
"""

from unittest.mock import patch

from langgraph.store.sqlite.aio import AsyncSqliteStore

from app.processing.agent import AgentOrchestrator
from app.processing.memory import StoreMemoryManager

# ── Nível de store (AsyncSqliteStore + StoreMemoryManager) ────────────────────


async def test_facts_persist_after_store_restart(tmp_path):
    """
    Fatos salvos por uma instância do AsyncSqliteStore devem ser acessíveis
    por uma nova instância apontando para o mesmo arquivo — simula restart.
    """
    db_path = str(tmp_path / "memory.db")

    # Instância 1: salva fatos e fecha
    async with AsyncSqliteStore.from_conn_string(db_path) as store:
        await store.setup()
        manager = StoreMemoryManager(store)
        await manager.save_fact("user_x", "k1", "[Interesse] Machine Learning")
        await manager.save_fact("user_x", "k2", "[Linguagem] Python avançado")

    # Instância 2: nova conexão ao mesmo arquivo (simula restart do servidor)
    async with AsyncSqliteStore.from_conn_string(db_path) as store:
        await store.setup()
        manager = StoreMemoryManager(store)
        facts = await manager.list_facts("user_x")

    assert len(facts) == 2, f"Esperado 2 fatos após restart, encontrado {len(facts)}"
    keys = {f["key"] for f in facts}
    assert keys == {"k1", "k2"}


async def test_facts_scoped_by_thread_persist_after_restart(tmp_path):
    """
    Fatos com thread_id também devem persistir, mantendo o namespace correto.
    """
    db_path = str(tmp_path / "memory.db")

    async with AsyncSqliteStore.from_conn_string(db_path) as store:
        await store.setup()
        manager = StoreMemoryManager(store)
        await manager.save_fact("user_y", "k1", "[Projeto] API REST", thread_id="t1")
        await manager.save_fact("user_y", "k2", "[Framework] FastAPI", thread_id="t1")

    async with AsyncSqliteStore.from_conn_string(db_path) as store:
        await store.setup()
        manager = StoreMemoryManager(store)
        facts = await manager.list_facts("user_y", thread_id="t1")

    assert len(facts) == 2
    keys = {f["key"] for f in facts}
    assert keys == {"k1", "k2"}


async def test_user_namespaces_are_isolated_after_restart(tmp_path):
    """
    Fatos de usuários distintos não devem se misturar após restart.
    """
    db_path = str(tmp_path / "memory.db")

    async with AsyncSqliteStore.from_conn_string(db_path) as store:
        await store.setup()
        manager = StoreMemoryManager(store)
        await manager.save_fact("alice", "a1", "[Projeto] Sistema de recomendação")
        await manager.save_fact("bob", "b1", "[Projeto] Análise de sentimento")

    async with AsyncSqliteStore.from_conn_string(db_path) as store:
        await store.setup()
        manager = StoreMemoryManager(store)
        alice_facts = await manager.list_facts("alice")
        bob_facts = await manager.list_facts("bob")

    assert len(alice_facts) == 1
    assert "recomendação" in alice_facts[0]["fact"]
    assert len(bob_facts) == 1
    assert "sentimento" in bob_facts[0]["fact"]


# ── Nível de AgentOrchestrator ────────────────────────────────────────────────


async def test_orchestrator_uses_async_sqlite_store_by_default(tmp_path):
    """
    AgentOrchestrator sem store explícito deve criar um AsyncSqliteStore
    (e não um InMemoryStore), garantindo persistência entre restarts.
    """
    db_path = str(tmp_path / "memory.db")

    import app.processing.agent as agent_module

    with patch.object(agent_module.settings, "MEMORY_DB_PATH", db_path):
        orchestrator = AgentOrchestrator()
        await orchestrator._ensure_initialized()
        try:
            assert isinstance(orchestrator.store, AsyncSqliteStore), (
                "AgentOrchestrator deve usar AsyncSqliteStore por padrão, não InMemoryStore."
            )
            assert orchestrator.store_manager is not None
        finally:
            await orchestrator.close()


async def test_orchestrator_memory_persists_between_instances(tmp_path):
    """
    Fatos salvos por uma instância do AgentOrchestrator devem ser acessíveis
    por uma nova instância apontando para o mesmo DB — critério central do B-002.
    """
    db_path = str(tmp_path / "memory.db")

    import app.processing.agent as agent_module

    with patch.object(agent_module.settings, "MEMORY_DB_PATH", db_path):
        # Instância 1: salva fatos e encerra
        orchestrator1 = AgentOrchestrator()
        await orchestrator1._ensure_initialized()
        await orchestrator1.store_manager.save_fact(
            "user_persist", "f1", "[Interesse] Redes Neurais"
        )
        await orchestrator1.store_manager.save_fact(
            "user_persist", "f2", "[Experiência] 3 anos com PyTorch"
        )
        await orchestrator1.close()

        # Instância 2 (simula restart): verifica que os fatos sobreviveram
        orchestrator2 = AgentOrchestrator()
        await orchestrator2._ensure_initialized()
        facts = await orchestrator2.store_manager.list_facts("user_persist")
        await orchestrator2.close()

    assert len(facts) == 2, (
        f"Esperado 2 fatos após restart do orchestrator, encontrado {len(facts)}. "
        "Verifique se AgentOrchestrator usa AsyncSqliteStore em vez de InMemoryStore."
    )
    keys = {f["key"] for f in facts}
    assert keys == {"f1", "f2"}
