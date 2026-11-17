"""BFF do portal de prefeitura e escola."""

import os
import uuid

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse


app = FastAPI(title="CampoConecta - BFF Prefeitura", version="1.0.0")
EDITAIS_URL = os.environ.get("EDITAIS_URL", "http://editais:8000").rstrip("/")
COMPRAS_URL = os.environ.get("COMPRAS_URL", "http://compras:8000").rstrip("/")
ENTREGAS_URL = os.environ.get("ENTREGAS_URL", "http://entregas:8000").rstrip("/")
TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "2"))


@app.middleware("http")
async def correlation(request: Request, call_next):
    try:
        correlation_id = str(uuid.UUID(request.headers.get("x-correlation-id", "")))
    except ValueError:
        correlation_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


def auth_role(headers: Header) -> str:
    return headers.get("x-authenticated-role", "")


async def consulta(base: str, caminho: str, authorization: str | None, correlation_id: str):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{base}/api/v1/{caminho}",
                headers={
                    "Authorization": authorization or "",
                    "X-Correlation-Id": correlation_id,
                },
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=503, detail="Fonte interna indisponível.")
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Fonte interna indisponível.") from exc


@app.get("/health")
def health():
    return {"status": "ok", "servico": "bff-prefeitura"}


@app.get("/api/v1/dashboard")
async def dashboard(
    request: Request,
    authorization: str | None = Header(default=None),
    x_authenticated_role: str | None = Header(default=None),
):
    if x_authenticated_role not in {"gestor", "escola"}:
        raise HTTPException(status_code=403, detail="Papel não autorizado.")
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))

    editais = await consulta(EDITAIS_URL, "editais?pagina=1&tamanho=50&status=PUBLICADO",
                             authorization, correlation_id)
    return {
        "cliente": "prefeitura",
        "papel": x_authenticated_role,
        "dashboard": {
            "editaisPublicados": editais.get("paginacao", {}).get("total", 0),
            "itens": editais.get("items", [])[:10],
        },
        "fontes": ["editais", "compras", "entregas"],
    }
