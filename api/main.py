from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Literal

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

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat")
def chat(req: RequisicaoChat):

    def gen():
        yield "IBIA: pensando...\n"

        
        from api.core_ibIA import buscar_contexto, stream_resposta_ibIA

        try:
            contexto = buscar_contexto(req.message)

            for parte in stream_resposta_ibIA(
                pergunta=req.message,
                historico=[{"role": m.role, "content": m.content} for m in req.history],
                contexto=contexto,
            ):
                yield str(parte)

        except Exception as e:
            yield f"\n[ERRO] {type(e).__name__}: {e}\n"

    return StreamingResponse(
        gen(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

