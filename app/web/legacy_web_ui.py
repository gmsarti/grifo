import streamlit as st
import httpx
import asyncio

# Interface do Utilizador (Presentation Layer)
st.set_page_config(page_title="Agente API-First", layout="centered")

st.title("🤖 Chat com Agente (3-Tier)")
st.caption("A comunicar com a API FastAPI em background.")

# Inicializa o histórico de chat na sessão do Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

# Desenha as mensagens antigas
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


async def fetch_agent_response(prompt: str) -> str:
    """Faz um pedido HTTP POST à nossa própria API (FastAPI)."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"message": prompt},
            timeout=120.0,  # LLMs podem demorar a responder
        )
        response.raise_for_status()
        return response.json()["response"]


# Captura a entrada do utilizador
if prompt := st.chat_input("Faça uma pergunta ao agente..."):
    # Adiciona e mostra a mensagem do utilizador
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Mostra o indicador de carregamento e busca a resposta
    with st.chat_message("assistant"):
        with st.spinner("O agente está a pensar e a consultar ferramentas..."):
            try:
                answer = asyncio.run(fetch_agent_response(prompt))
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
            except Exception as e:
                st.error(f"Erro de comunicação com a API: {e}")
