"""
Testa a captura de fatos e memória de longo prazo do Grifo.

Uso:
    uv run python scripts/test_memory.py
"""

import asyncio
import uuid

import httpx

BASE = "http://localhost:8000"
THREAD_ID = str(uuid.uuid4())
USER_ID = "test_memory_user"
PROJECT_ID = "test_memory"

MESSAGES = [
    "Oi! Me chamo Gustavo e sou desenvolvedor de software.",
    "Minha linguagem favorita é Python, mas também uso Go no trabalho.",
    "Tenho um projeto pessoal de agente de IA chamado Grifo.",
]


async def chat(client: httpx.AsyncClient, message: str) -> str:
    r = await client.post(
        f"{BASE}/api/v1/chat",
        json={
            "message": message,
            "project_id": PROJECT_ID,
            "thread_id": THREAD_ID,
            "user_id": USER_ID,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["response"]


async def get_facts(client: httpx.AsyncClient) -> list[dict]:
    r = await client.get(
        f"{BASE}/api/v1/memory/{THREAD_ID}/facts",
        params={"user_id": USER_ID},
    )
    r.raise_for_status()
    return r.json().get("facts", [])


async def wait_for_api(client: httpx.AsyncClient, timeout: int = 60) -> None:
    print("Aguardando API...", end="", flush=True)
    for _ in range(timeout):
        try:
            r = await client.get(f"{BASE}/api/health", timeout=2)
            if r.status_code == 200:
                print(" pronta!\n")
                return
        except Exception:
            pass
        print(".", end="", flush=True)
        await asyncio.sleep(1)
    raise RuntimeError(
        f"API não respondeu após {timeout}s. Certifique-se de que o servidor está rodando."
    )


async def main():
    print(f"Thread ID : {THREAD_ID}")
    print(f"User ID   : {USER_ID}\n")

    async with httpx.AsyncClient() as client:
        await wait_for_api(client)

        # Envia mensagens
        for msg in MESSAGES:
            print(f"→ {msg}")
            reply = await chat(client, msg)
            print(f"← {reply[:120]}{'...' if len(reply) > 120 else ''}\n")

        # Verifica fatos capturados
        facts = await get_facts(client)
        print("─" * 60)
        if not facts:
            print("✗ Nenhum fato capturado.")
        else:
            print(f"✓ {len(facts)} fato(s) capturado(s):\n")
            for f in facts:
                fact_text = f.get("fact", str(f))
                print(f"  • {fact_text}")


if __name__ == "__main__":
    asyncio.run(main())
