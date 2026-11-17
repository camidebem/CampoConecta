import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import db, erros, migracoes
from .config import carregar
from .rotas import router

config = carregar()
logging.basicConfig(
    level=config.log_level,
    format=f"%(asctime)s %(levelname)s [{config.servico}] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    migracoes.aplicar(config.database_url)
    db.abrir(config)
    yield
    db.fechar()


app = FastAPI(
    title="CampoConecta — Serviço de Ofertas",
    version="1.0.0",
    description="Produtores da agricultura familiar e suas ofertas de produção.",
    lifespan=lifespan,
)
erros.registrar(app)


@app.middleware("http")
async def correlacao(request: Request, call_next):
    """Propaga X-Correlation-Id (UUID válido) ou gera um novo."""
    try:
        cid = str(uuid.UUID(request.headers.get("x-correlation-id", "")))
    except ValueError:
        cid = str(uuid.uuid4())
    request.state.correlation_id = cid
    resposta = await call_next(request)
    resposta.headers["X-Correlation-Id"] = cid
    return resposta


@app.get("/health", tags=["operação"])
def health():
    """200 se o banco do serviço responde; 503 caso contrário."""
    try:
        with db.conexao(timeout=2) as conn:
            conn.execute("SELECT 1")
    except Exception:
        return JSONResponse(status_code=503,
                            content={"status": "indisponivel", "servico": config.servico, "banco": "falha"})
    return {"status": "ok", "servico": config.servico, "banco": "ok"}


app.include_router(router, prefix="/api/v1")
