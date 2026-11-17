"""Formato único de erro, conforme o schema `Erro` dos contratos OpenAPI:
{ "code", "message", "details": [{ "campo", "motivo" }], "correlationId" }
"""

import logging
import uuid

import psycopg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg_pool import PoolTimeout
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger(__name__)


class ErroApi(Exception):
    def __init__(self, status: int, code: str, message: str, details: list[dict] | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", None) or str(uuid.uuid4())


def resposta_erro(request: Request, status: int, code: str, message: str, details=None) -> JSONResponse:
    cid = correlation_id(request)
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message, "details": details or [], "correlationId": cid},
        headers={"X-Correlation-Id": cid},
    )


_CODIGOS_HTTP = {
    404: ("NAO_ENCONTRADO", "Recurso não encontrado."),
    405: ("METODO_NAO_PERMITIDO", "Método não permitido para este recurso."),
}


def registrar(app: FastAPI) -> None:
    @app.exception_handler(ErroApi)
    async def _erro_api(request: Request, exc: ErroApi):
        return resposta_erro(request, exc.status, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validacao(request: Request, exc: RequestValidationError):
        details = [
            {"campo": ".".join(str(p) for p in e["loc"]) or "requisicao", "motivo": e["msg"]}
            for e in exc.errors()
        ]
        return resposta_erro(request, 400, "REQUISICAO_INVALIDA", "Dados da requisição inválidos.", details)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code, message = _CODIGOS_HTTP.get(exc.status_code, ("ERRO_HTTP", str(exc.detail)))
        return resposta_erro(request, exc.status_code, code, message)

    @app.exception_handler(PoolTimeout)
    @app.exception_handler(psycopg.OperationalError)
    async def _banco_indisponivel(request: Request, exc: Exception):
        log.error("Banco indisponível: %s", exc)
        return resposta_erro(request, 503, "SERVICO_INDISPONIVEL", "Banco de dados indisponível no momento.")
