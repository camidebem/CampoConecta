"""Idempotency-Key para os POST de criação (contrato da Parte 2).

A chave é registrada NA MESMA TRANSAÇÃO da escrita de negócio:
- primeira vez: grava a chave, executa a ação e guarda status/corpo/Location;
- reenvio idêntico: devolve a resposta original, sem executar de novo;
- mesma chave com corpo diferente: 409.
Se a ação falhar, a transação inteira é desfeita e a chave não fica registrada.
Duas requisições simultâneas com a mesma chave: a segunda espera o COMMIT da
primeira (unicidade da chave) e então recebe a resposta gravada.

Limitação desta etapa: o escopo ainda não inclui o `sub` autenticado
(a autenticação na borda é feita pelo gateway/authn-verify).
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from psycopg.types.json import Jsonb

from . import db
from .erros import ErroApi, correlation_id


@dataclass
class Resultado:
    status: int
    corpo: dict
    location: str | None = None


def executar(request: Request, chave: uuid.UUID, corpo: dict, acao: Callable) -> JSONResponse:
    metodo = request.method
    caminho = request.url.path
    hash_corpo = hashlib.sha256(json.dumps(corpo, sort_keys=True, default=str).encode()).hexdigest()

    with db.conexao() as conn:
        nova = conn.execute(
            "INSERT INTO idempotencia (chave, metodo, caminho, hash_corpo) VALUES (%s, %s, %s, %s)"
            " ON CONFLICT DO NOTHING RETURNING chave",
            (chave, metodo, caminho, hash_corpo),
        ).fetchone()

        if nova is None:
            anterior = conn.execute(
                "SELECT hash_corpo, status, corpo, location FROM idempotencia"
                " WHERE chave = %s AND metodo = %s AND caminho = %s",
                (chave, metodo, caminho),
            ).fetchone()
            if anterior["hash_corpo"] != hash_corpo or anterior["status"] is None:
                raise ErroApi(409, "IDEMPOTENCIA_CONFLITO",
                              "Idempotency-Key já usada com outro conteúdo.")
            return _responder(request, Resultado(anterior["status"], anterior["corpo"], anterior["location"]),
                              repetida=True)

        resultado: Resultado = acao(conn)
        conn.execute(
            "UPDATE idempotencia SET status = %s, corpo = %s, location = %s"
            " WHERE chave = %s AND metodo = %s AND caminho = %s",
            (resultado.status, Jsonb(resultado.corpo), resultado.location, chave, metodo, caminho),
        )
    return _responder(request, resultado, repetida=False)


def _responder(request: Request, r: Resultado, repetida: bool) -> JSONResponse:
    headers = {"X-Correlation-Id": correlation_id(request)}
    if r.location:
        headers["Location"] = r.location
    if repetida:
        headers["Idempotent-Replayed"] = "true"
    return JSONResponse(status_code=r.status, content=r.corpo, headers=headers)
