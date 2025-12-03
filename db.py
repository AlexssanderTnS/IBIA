from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma  
from langchain_huggingface import HuggingFaceEmbeddings  
from dotenv import load_dotenv

load_dotenv()

PASTA_BASE = "base"

def criar_db():
    documentos = carregar_documentos()
    print(documentos)
    chunks = dividir_chunks(documentos)
    vetorizar_chunks(chunks)    

def carregar_documentos():
    carregador = PyPDFDirectoryLoader(PASTA_BASE, glob="*.pdf")
    documentos = carregador.load()
    return documentos

def dividir_chunks(documentos):
    separador_documentos = RecursiveCharacterTextSplitter(
        chunk_size=3000,      # antes 3000
        chunk_overlap=500,   # mantém um pouco de contexto
        length_function=len,
    )
    chunks = separador_documentos.split_documents(documentos)
    print(f"Número de chunks: {len(chunks)}")
    return chunks

def vetorizar_chunks(chunks):
    embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


    db = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory="DB"
    )

    print("Banco de dados vetorial criado com sucesso!")

criar_db()
