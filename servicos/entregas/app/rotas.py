"""Capacidades persistidas; agendamento e recebimento entram com a SAGA."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, Request

from . import db, idempotencia
from .erros import ErroApi
from .idempotencia import Resultado
from .modelos import CapacidadeCriacao

router = APIRouter()


def _capacidade(linha: dict) -> dict:
    return {
        "id": str(linha["id"]), "escolaId": str(linha["escola_id"]),
        "janela": {"inicio": linha["janela_inicio"].isoformat(), "fim": linha["janela_fim"].isoformat()},
        "capacidadeKg": format(linha["capacidade_kg"], ".2f"),
        "reservadoKg": format(linha["reservado_kg"], ".2f"), "versao": linha["versao"],
    }


@router.post("/capacidades", status_code=201, tags=["capacidades"])
def criar_capacidade(dados: CapacidadeCriacao, request: Request,
                     idempotency_key: UUID = Header(alias="Idempotency-Key")):
    def acao(conn):
        # Validado após a consulta de idempotência: um reenvio deve recuperar
        # a resposta original mesmo quando a janela já tiver começado.
        if dados.janela.inicio <= datetime.now(timezone.utc):
            raise ErroApi(400, "JANELA_INVALIDA", "A janela deve começar no futuro.")
        # Serializa a verificação por escola, inclusive entre réplicas do serviço.
        # Colisões do hash só serializam escolas extras; não afetam a correção.
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (str(dados.escolaId),))
        sobreposta = conn.execute(
            "SELECT 1 FROM capacidade_logistica WHERE escola_id = %s"
            " AND janela_inicio < %s AND janela_fim > %s LIMIT 1",
            (dados.escolaId, dados.janela.fim, dados.janela.inicio),
        ).fetchone()
        if sobreposta:
            raise ErroApi(409, "JANELA_SOBREPOSTA", "Já existe capacidade nesta janela para a escola.")
        linha = conn.execute(
            "INSERT INTO capacidade_logistica (id, escola_id, janela_inicio, janela_fim, capacidade_kg)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (uuid.uuid4(), dados.escolaId, dados.janela.inicio, dados.janela.fim, Decimal(dados.capacidadeKg)),
        ).fetchone()
        return Resultado(201, _capacidade(linha), f"/api/v1/capacidades/{linha['id']}")

    return idempotencia.executar(request, idempotency_key, dados.model_dump(mode="json"), acao)


@router.get("/capacidades/{id}", tags=["capacidades"])
def obter_capacidade(id: UUID):
    with db.conexao() as conn:
        linha = conn.execute("SELECT * FROM capacidade_logistica WHERE id = %s", (id,)).fetchone()
    if linha is None:
        raise ErroApi(404, "CAPACIDADE_NAO_ENCONTRADA", "Capacidade não encontrada.")
    return _capacidade(linha)
