import streamlit as st
from core_ibIA import buscar_contexto, gerar_resposta_ibIA

st.set_page_config(page_title="IBIA - Assistente CNH", page_icon="🚗")

st.title("IBIA - Assistente Virtual de CNH")


if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = [
        {
            "role": "assistant",
            "content": (
                "Olá! Eu sou a **IBIA**, sua assistente virtual de educação para o trânsito. "
                "Posso te ajudar com dúvidas sobre CNH, leis de trânsito, direção defensiva "
                "e conteúdos da sua apostila. O que você gostaria de saber hoje?"
            ),
        }
    ]


for msg in st.session_state["mensagens"]:
    avatar = "assets/IBIA.png" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


pergunta = st.chat_input("Digite sua dúvida sobre CNH:")

if pergunta:
    #
    st.session_state["mensagens"].append(
        {"role": "user", "content": pergunta}
    )

    
    with st.chat_message("user", avatar="👤"):
        st.markdown(pergunta)


    with st.spinner("Buscando conteúdo relacionado nos materiais..."):
        contexto = buscar_contexto(pergunta)

    
    with st.chat_message("assistant", avatar="assets/IBIA.png"):
        with st.spinner("IBIA está pensando..."):
            try:
                resposta = gerar_resposta_ibIA(
                    pergunta=pergunta,
                    historico=st.session_state["mensagens"],
                    contexto=contexto,
                )
                st.markdown(resposta)
            except Exception as e:
                resposta = f"Erro: `{e}`"
                st.error(resposta)


    st.session_state["mensagens"].append(
        {"role": "assistant", "content": resposta}
    )
