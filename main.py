import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


db = Chroma(persist_directory="DB", embedding_function=embeddings)

# LLM do Ollama
llm = ChatOllama(
    model="phi3:mini",   
    temperature=0.2,
    options={"num_ctx": 4096}
)

prompt = ChatPromptTemplate.from_template(
    """
Você é uma instrutora de trânsito chamada IBIA, especializada em CNH e dicas de como tirar a primeira habilitação.
Responda SEMPRE em português claro, didático e objetivo. sempre fale me português do Brasil.

Use APENAS as informações do CONTEXTO abaixo.
Se o contexto não trouxer a resposta, diga que o material não é suficiente
e sugira que o aluno procure o instrutor.

---------------- CONTEXTO ----------------
{context}
-----------------------------------------

PERGUNTA DO ALUNO:
{question}

RESPOSTA completa em linguagem simples(sempre em pt-br):
"""
)

st.title("Assistente IBIA - Perguntas sobre CNH")

pergunta = st.text_input("Digite sua pergunta:")

if st.button("Perguntar"):
    if pergunta.strip() == "":
        st.warning("Digite algo.")
    else:
      
        resultados = db.similarity_search_with_score(pergunta, k=8)

       
        limite_score = 0.55  

        relevantes = [(doc, score) for doc, score in resultados if score <= limite_score]

        st.subheader("Trechos mais relevantes:")

        if not relevantes:
            st.write("Nenhum trecho com relevância suficiente foi encontrado.")
            contexto = ""  #
        else:
            partes_contexto = []
            for i, (doc, score) in enumerate(relevantes, start=1):
                st.markdown(f"**Trecho {i}** (score: `{score:.3f}`)")
                st.write(doc.page_content)        
               
                st.markdown("---")
                partes_contexto.append(doc.page_content)

            
            contexto = "\n\n".join(partes_contexto)

        st.subheader("Resposta:")

        if not contexto:
            st.write(
                "Não encontrei trechos suficientes no material para responder com segurança "
                "sobre esse assunto."
            )
        else:
            
            chain = prompt | llm
            resposta = chain.invoke(
                {
                    "context": contexto,
                    "question": pergunta,
                }
            ).content

            st.write(resposta)
