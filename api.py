from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal, Dict

from core_ibIA import buscar_contexto, gerar_resposta_ibIA

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # por enquanto; depois restringe pro domínio do Moodle/widget
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    
class RequisicaoChat(BaseModel):
    message:str
    history: List[Mensagem] = []
    
    
@app.get("/")
def raiz():
    return{"mensagem": "API da IBIA está no ar!"}

@app.post("/chat")
def chat(req: RequisicaoChat):
    contexto = buscar_contexto(req.message)
    
    historico = [msg.model_dump() for msg in req.history]
    
    resposta = gerar_resposta_ibIA(
        pergunta=req.message,
        historico=historico,
        contexto=contexto,
    )
    
    return {
        "reply" : resposta
    }