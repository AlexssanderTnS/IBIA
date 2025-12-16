import os
from dotenv import load_dotenv
from groq import Groq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não encontrada. Defina no .env ou nas variáveis de ambiente.")


client = Groq(api_key=GROQ_API_KEY)


embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5", 
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "DB")
db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)


SYSTEM_MSG = """
Você é a IBIA — Inteligência Baseada em Instrução Automotiva.

É uma instrutora virtual de trânsito, especialista em CNH, legislação, direção defensiva
e educação para o trânsito.

Regras gerais de comportamento:
- Responda SEMPRE em português do Brasil.
- Seja clara, simples, amigável e profissional.
- Explique em linguagem acessível, como se estivesse conversando com um aluno iniciante.

Uso de contexto:
- Use APENAS o CONTEXTO fornecido abaixo para responder ao aluno.
- Se o CONTEXTO não trouxer a resposta, NÃO tente “adivinhar”.
- Nesses casos, diga claramente que o material não é suficiente
  e recomende procurar um instrutor ou material complementar.

Limites de assunto:
- Você SÓ responde dúvidas relacionadas a:
    • CNH (todas as categorias),
    • legislação de trânsito,
    • sinalização,
    • direção defensiva,
    • primeiros socorros no trânsito,
    • meio ambiente e cidadania no trânsito,
    • conteúdos oficiais da apostila de trânsito.
- Se o aluno fizer perguntas sobre qualquer outro tema
  que não seja trânsito, responda:
  "Sou uma assistente focada apenas em educação para o trânsito e CNH. Essa pergunta foge do meu escopo."
- Nunca analise, corrija ou comente trechos de código de programação, mesmo que o aluno envie
  código na conversa.
- Nunca explique o funcionamento interno da própria IBIA, de modelos de IA ou da infraestrutura técnica.
  Seu foco é SEMPRE o conteúdo de trânsito e da CNH.

Objetivo:
- Ajudar o aluno a entender melhor os conteúdos de trânsito, reforçando a aprendizagem
  e preparando para as provas teóricas e para a condução responsável.
"""


def buscar_contexto(pergunta: str, k: int = 6, limite_score: float = 0.55) -> str:
    """
    Faz a busca no banco vetorial (Chroma) usando a pergunta do aluno
    e devolve um texto com os trechos mais relevantes concatenados.
    """
   
    resultados = db.similarity_search_with_score(pergunta, k=k)
    relevantes = [(doc, score) for doc, score in resultados if score <= limite_score]

    if not relevantes:
        return ""

    partes = [doc.page_content for doc, score in relevantes]
    contexto = "\n\n".join(partes)
    return contexto


def gerar_resposta_ibIA(pergunta: str, historico: list, contexto: str = "") -> str:
    """
    Gera uma resposta completa da IBIA.
    - pergunta: texto do aluno
    - historico: lista de mensagens no formato [{"role": "user"/"assistant", "content": "..."}]
    - contexto: texto vindo do RAG (opcional; se vazio, IBIA assume que não há material suficiente)
    """

    mensagens = [
        {"role": "system", "content": SYSTEM_MSG}
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
        model="llama-3.1-8b-instant",  
        messages=mensagens,
        temperature=0.5,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()

def stream_resposta_ibIA(pergunta: str, historico: list, contexto: str = ""):
    mensagens = [{"role": "system", "content": SYSTEM_MSG}]

    for msg in historico[-6:]:
        if msg["role"] in ("user", "assistant"):
            mensagens.append({"role": msg["role"], "content": msg["content"]})

    user_msg = f"""
------------------- CONTEXTO -------------------
{contexto}
------------------------------------------------

Pergunta do aluno:
{pergunta}

Responda como IBIA:
"""
    mensagens.append({"role": "user", "content": user_msg})

    resposta_stream = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=mensagens,
        temperature=0.5,
        max_tokens=800,
        stream=True,
    )

    for chunk in resposta_stream:
        parte = getattr(chunk.choices[0].delta, "content", None)
        if parte:
            yield parte

