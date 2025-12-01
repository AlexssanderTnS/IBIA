import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Carregar embeddings (mesmo modelo usado no db.py)
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

# Carregar o Chroma
db = Chroma(persist_directory="DB", embedding_function=embeddings)

st.title("Assistente IBIA - Perguntas sobre CNH")

pergunta = st.text_input("Digite sua pergunta:")

if st.button("Perguntar"):
    if pergunta.strip() == "":
        st.warning("Digite algo.")
    else:
        # PEGAR RESULTADOS COM SCORE
        resultados = db.similarity_search_with_score(pergunta, k=8)

        # No Chroma, score menor = mais parecido
        limite_score = 0.55  # mais flexível que 0.35

        # st.write("SCORES encontrados:")
        # for doc, score in resultados:
        #     st.write(f"{score:.4f} → {doc.page_content[:120]}...")

        # # filtrar só os relevantes
        relevantes = [(doc, score) for doc, score in resultados if score <= limite_score]

        st.subheader("Trechos mais relevantes:")

        if not relevantes:
            st.write("Nenhum trecho com relevância suficiente foi encontrado.")
        else:
            for i, (doc, score) in enumerate(relevantes, start=1):
                st.markdown(f"**Trecho {i}** (score: `{score:.3f}`)")
                st.write(doc.page_content)
                # st.caption(str(doc.metadata))
                st.markdown("---")

        st.subheader("Resposta:")
        resposta = "Esta é uma resposta simulada baseada nos trechos fornecidos."
        st.write(resposta)

