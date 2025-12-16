from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Literal

from core_ibIA import buscar_contexto, stream_resposta_ibIA  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class RequisicaoChat(BaseModel):
    message: str
    history: List[Mensagem] = []

@app.get("/")
def raiz():
    return {"mensagem": "API da IBIA está no ar!"}

@app.post("/chat")
def chat(req: RequisicaoChat):
    message = req.message

    # Converte Mensagem (Pydantic) -> dict
    history = [{"role": m.role, "content": m.content} for m in req.history]

    contexto = buscar_contexto(message)

    def gen():
        for parte in stream_resposta_ibIA(message, contexto, history):
            yield parte

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")
