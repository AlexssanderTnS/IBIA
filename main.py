import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama


embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

db = Chroma(persist_directory="DB", embedding_function=embeddings)



def gerar_resposta_ibIA(pergunta: str, contexto: str) -> str:
    llm = ChatOllama(
        model="phi3:mini", 
        temperature=0.2,
    )

    prompt = f"""
Você é a IBIA — Inteligência Baseada em Instrução Automotiva.

É uma instrutora virtual de trânsito, especialista em CNH, legislação, direção defensiva
e educação para o trânsito.

Regras:
- Responda SEMPRE em português do Brasil.
- Seja clara, simples, amigável e profissional.
- Use APENAS o CONTEXTO fornecido abaixo para responder.
- Se o contexto não trouxer a resposta, diga claramente que o material não é suficiente
  e recomende procurar um instrutor ou material complementar.
- Explique em linguagem acessível, como se estivesse conversando com um aluno.

------------------- CONTEXTO -------------------
{contexto}
------------------------------------------------

Pergunta do aluno:
{pergunta}

Resposta da IBIA:
"""

    resultado = llm.invoke(prompt)
    return getattr(resultado, "content", str(resultado))



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
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


pergunta = st.chat_input("Digite sua dúvida sobre CNH:")

if pergunta:

    st.session_state["mensagens"].append(
        {"role": "user", "content": pergunta}
    )


    with st.chat_message("user"):
        st.markdown(pergunta)


    resultados = db.similarity_search_with_score(pergunta, k=6)
    limite_score = 0.55
    relevantes = [(doc, score) for doc, score in resultados if score <= limite_score]

    if not relevantes:
        resposta = (
            "Não encontrei informações suficientes nos materiais carregados para responder "
            "com segurança à sua pergunta. Recomendo consultar seu instrutor ou material "
            "complementar da autoescola."
        )
    else:
        partes_contexto = [doc.page_content for doc, score in relevantes]
        contexto = "\n\n".join(partes_contexto)


        with st.chat_message("assistant"):
            with st.spinner("IBIA está pensando..."):
                try:
                    resposta = gerar_resposta_ibIA(pergunta, contexto)
                    st.markdown(resposta)
                except Exception as e:
                    resposta = f"Erro ao gerar resposta com o modelo local: `{e}`"
                    st.error(resposta)

    
    st.session_state["mensagens"].append(
        {"role": "assistant", "content": resposta}
    )
