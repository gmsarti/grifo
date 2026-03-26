import asyncio
import os

from app.core.config import settings
from app.processing.agent import AgentOrchestrator


async def test_persistence():
    # Use a temporary DB for this test
    test_db = "./data/test_persistence.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    settings.MEMORY_DB_PATH = test_db

    print("--- Session 1: Saving fact ---")
    orchestrator1 = AgentOrchestrator()
    await orchestrator1._ensure_initialized()
    user_id = "test_user"
    fact_key = "pref_color"
    fact_value = "User likes blue"

    await orchestrator1.store_manager.save_fact(user_id, fact_key, fact_value)
    print(f"Saved fact: {fact_value}")

    # Check if it was saved index-wise (SqliteStore handles asearch)
    mems = await orchestrator1.store_manager.search_memories(user_id, "color")
    print(f"Search results in Session 1: {[m.value['content'] for m in mems]}")
    assert len(mems) > 0

    print("\n--- Session 2: New instance, same DB ---")
    orchestrator2 = AgentOrchestrator()
    await orchestrator2._ensure_initialized()
    mems2 = await orchestrator2.store_manager.search_memories(user_id, "color")
    print(f"Search results in Session 2: {[m.value['content'] for m in mems2]}")

    if len(mems2) > 0 and mems2[0].value["content"] == fact_value:
        print("\nSUCCESS: Fact persisted across instances!")
    else:
        print("\nFAILURE: Fact did not persist.")
        exit(1)

    print("\n--- Session 3: Checkpointing (Thread History) ---")
    # This is harder to test without a full graph run, but we can check if it initializes
    # If the app starts and can invoke without error, it's a good sign.

    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)


if __name__ == "__main__":
    asyncio.run(test_persistence())
