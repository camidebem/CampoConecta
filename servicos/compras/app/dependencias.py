"""Consultas HTTP aos donos dos dados, sem acesso aos bancos alheios."""

import json
import os
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request as HttpRequest, urlopen

from fastapi import Request

from .erros import ErroApi, correlation_id


def consultar(servico: str, caminho: str, request: Request) -> dict:
    base = os.environ.get(f"{servico.upper()}_URL", f"http://{servico}:8000").rstrip("/")
    headers = {"Accept": "application/json", "X-Correlation-Id": correlation_id(request)}
    if request.headers.get("authorization"):
        headers["Authorization"] = request.headers["authorization"]
    requisicao = HttpRequest(f"{base}/api/v1/{caminho}", headers=headers)
    try:
        with urlopen(requisicao, timeout=float(os.environ.get("HTTP_TIMEOUT", "2"))) as resposta:
            dados = json.load(resposta)
        if not isinstance(dados, dict):
            raise ValueError("Resposta não é um objeto JSON.")
        return dados
    except HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise ErroApi(exc.code, "REFERENCIA_INACESSIVEL",
                          f"Recurso indisponível para consulta em {servico}.") from exc
        raise ErroApi(503, "DEPENDENCIA_INDISPONIVEL",
                      f"Não foi possível consultar {servico}.") from exc
    except (URLError, TimeoutError, OSError, ValueError, HTTPException) as exc:
        raise ErroApi(503, "DEPENDENCIA_INDISPONIVEL",
                      f"Não foi possível consultar {servico}.") from exc
