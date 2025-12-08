import csv
import requests
import json
from datetime import datetime
import os
import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


FEEDBACK_EMAIL_ENDPOINT = "https://formsubmit.co/alexssander.amat@gmail.com?noCaptcha=true"

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

db = Chroma(persist_directory="DB", embedding_function=embeddings)


def gerar_resposta_ibIA(pergunta: str, contexto: str, historico) -> str:
    system_msg = """
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
"""

    mensagens = [
        {"role": "system", "content": system_msg}
    ]

    for msg in historico[-6:]:
        if msg["role"] in ("user", "assistant"):
            mensagens.append(
                {"role": msg["role"], "content": msg["content"]}
            )

    user_msg = f"""
------------------- CONTEXTO -------------------
{contexto}
------------------------------------------------

Pergunta do aluno:
{pergunta}

Responda como IBIA:
"""

    mensagens.append({"role": "user", "content": user_msg})

    response = client.chat.completions.create(
        model="groq/compound",
        messages=mensagens,
        temperature=0.5,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()


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

if "feedback_enviado" not in st.session_state:
    st.session_state["feedback_enviado"] = False

for msg in st.session_state["mensagens"]:
    avatar = "assets/IBIA.png" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

pergunta = st.chat_input("Digite sua dúvida sobre CNH:")

if pergunta:
    st.session_state["mensagens"].append(
        {"role": "user", "content": pergunta}
    )

    with st.chat_message("user", avatar="👤"):
        st.markdown(pergunta)

    resultados = db.similarity_search_with_score(pergunta, k=6)
    limite_score = 0.55
    relevantes = [(doc, score) for doc, score in resultados if score <= limite_score]

    if not relevantes:
        with st.chat_message("assistant", avatar="assets/IBIA.png"):
            with st.spinner("IBIA está pensando..."):
                try:
                    resposta = gerar_resposta_ibIA(
                        pergunta,
                        "",
                        st.session_state["mensagens"],
                    )
                    st.markdown(resposta)
                except Exception as e:
                    resposta = f"Erro: `{e}`"
                    st.error(resposta)
    else:
        partes_contexto = [doc.page_content for doc, score in relevantes]
        contexto = "\n\n".join(partes_contexto)

        with st.chat_message("assistant", avatar="assets/IBIA.png"):
            with st.spinner("IBIA está pensando..."):
                try:
                    resposta = gerar_resposta_ibIA(
                        pergunta,
                        contexto,
                        st.session_state["mensagens"],
                    )
                    st.markdown(resposta)
                except Exception as e:
                    resposta = f"Erro: `{e}`"
                    st.error(resposta)

    st.session_state["mensagens"].append(
        {"role": "assistant", "content": resposta}
    )

st.markdown("---")
st.subheader("Feedback sobre a IBIA")

if not st.session_state["feedback_enviado"]:
    with st.form("feedback_form"):
        nota = st.radio(
            "Como foi sua experiência com a IBIA hoje?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: f"{x}",
            horizontal=True,
        )
        
        comentario = st.text_area(
            "Quer deixar um comentário opcional?",
            placeholder="Conte no que podemos melhorar ou como a IBIA te ajudou hoje.",
        )

        enviar = st.form_submit_button("Enviar feedback")

    if enviar:
        linha = [
            datetime.now().isoformat(),
            nota,
            comentario,
        ]
        
        arquivo_csv = "feedback_ibia.csv"
        arquivo_existe = os.path.exists(arquivo_csv)
        
        with open(arquivo_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not arquivo_existe:
                writer.writerow(["timestamp", "nota", "comentario"])
            writer.writerow(linha)
            
        historico_arquivo = "historico_conversa.json"
        dados = {
            "timestamp": datetime.now().isoformat(),
            "mensagens": st.session_state["mensagens"],
            "nota": nota,
            "comentario": comentario,
        }
        
        if os.path.exists(historico_arquivo):
            with open(historico_arquivo, "r", encoding="utf-8") as f:
                try:
                    existente = json.load(f)
                except json.JSONDecodeError:
                    existente = []
        else:
            existente = []
            
        existente.append(dados)
        
        with open(historico_arquivo, "w", encoding="utf-8") as f:
            json.dump(existente, f, ensure_ascii=False, indent=2)

        try:
            requests.post(
                FEEDBACK_EMAIL_ENDPOINT,
                data={
                    "nota": nota,
                    "comentario": comentario,
                },
                timeout=10,
            )
        except Exception as e:
            st.warning("Seu feedback foi salvo, mas não consegui enviar o e-mail agora.")

        st.session_state["feedback_enviado"] = True
        st.success("Obrigado, seu feedback foi registrado com sucesso!")
else:
    st.info("Obrigado! Seu feedback foi registrado com sucesso.")
