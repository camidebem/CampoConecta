"""Endpoints do serviço Ofertas (subconjunto do contrato da Parte 2).

POST /produtores         GET /produtores/{id}
POST /ofertas            GET /ofertas             GET /ofertas/{id}
"""

import math
import uuid
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from psycopg import errors as pg_errors

from . import db, idempotencia
from .erros import ErroApi
from .idempotencia import Resultado
from .modelos import OfertaCriacao, ProdutorCriacao

router = APIRouter()


# ---------- serialização (banco -> contrato) ----------

def _produtor(l: dict) -> dict:
    return {"id": str(l["id"]), "nome": l["nome"], "documento": l["documento"],
            "email": l["email"], "ativo": l["ativo"], "versao": l["versao"]}


def _oferta(l: dict) -> dict:
    return {
        "id": str(l["id"]),
        "produtorId": str(l["produtor_id"]),
        "produto": l["produto"],
        "quantidadeDisponivel": {"valor": format(l["quantidade_disponivel"], ".2f"), "unidade": l["unidade"]},
        "ativa": l["ativa"],
        "versao": l["versao"],
    }


_NAO_ENCONTRADO = {
    "produtor": ("PRODUTOR_NAO_ENCONTRADO", "Produtor não encontrado."),
    "oferta": ("OFERTA_NAO_ENCONTRADA", "Oferta não encontrada."),
}


def _nao_encontrado(recurso: str) -> ErroApi:
    return ErroApi(404, *_NAO_ENCONTRADO[recurso])


# ---------- produtores ----------

@router.post("/produtores", status_code=201, tags=["produtores"])
def criar_produtor(dados: ProdutorCriacao, request: Request,
                   idempotency_key: UUID = Header(alias="Idempotency-Key")):
    def acao(conn):
        try:
            linha = conn.execute(
                "INSERT INTO produtor (id, nome, documento, email) VALUES (%s, %s, %s, %s) RETURNING *",
                (uuid.uuid4(), dados.nome, dados.documento, dados.email),
            ).fetchone()
        except pg_errors.UniqueViolation:
            raise ErroApi(409, "DOCUMENTO_JA_CADASTRADO", "Já existe produtor com este documento.",
                          [{"campo": "documento", "motivo": "duplicado"}])
        return Resultado(201, _produtor(linha), f"/api/v1/produtores/{linha['id']}")

    return idempotencia.executar(request, idempotency_key, dados.model_dump(mode="json"), acao)


@router.get("/produtores/{id}", tags=["produtores"])
def obter_produtor(id: UUID):
    with db.conexao() as conn:
        linha = conn.execute("SELECT * FROM produtor WHERE id = %s", (id,)).fetchone()
    if linha is None:
        raise _nao_encontrado("produtor")
    return _produtor(linha)


# ---------- ofertas ----------

@router.post("/ofertas", status_code=201, tags=["ofertas"])
def criar_oferta(dados: OfertaCriacao, request: Request,
                 idempotency_key: UUID = Header(alias="Idempotency-Key")):
    def acao(conn):
        produtor = conn.execute("SELECT ativo FROM produtor WHERE id = %s", (dados.produtorId,)).fetchone()
        if produtor is None:
            raise _nao_encontrado("produtor")
        if not produtor["ativo"]:
            raise ErroApi(409, "PRODUTOR_INATIVO", "Produtor inativo não pode cadastrar ofertas.")
        linha = conn.execute(
            "INSERT INTO oferta (id, produtor_id, produto, unidade, quantidade_disponivel)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (uuid.uuid4(), dados.produtorId, dados.produto, dados.quantidadeDisponivel.unidade,
             Decimal(dados.quantidadeDisponivel.valor)),
        ).fetchone()
        return Resultado(201, _oferta(linha), f"/api/v1/ofertas/{linha['id']}")

    return idempotencia.executar(request, idempotency_key, dados.model_dump(mode="json"), acao)


@router.get("/ofertas", tags=["ofertas"])
def listar_ofertas(
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=50),
    ativa: bool | None = None,
    produto: str | None = Query(None, min_length=1, max_length=200),
):
    filtros, params = [], []
    if ativa is not None:
        filtros.append("ativa = %s")
        params.append(ativa)
    if produto:
        filtros.append("produto = %s")
        params.append(produto)
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    with db.conexao() as conn:
        total = conn.execute(f"SELECT count(*) AS n FROM oferta {where}", params).fetchone()["n"]
        linhas = conn.execute(
            f"SELECT * FROM oferta {where} ORDER BY criado_em DESC, id LIMIT %s OFFSET %s",
            [*params, tamanho, (pagina - 1) * tamanho],
        ).fetchall()

    return {
        "items": [_oferta(l) for l in linhas],
        "paginacao": {"pagina": pagina, "tamanho": tamanho, "total": total,
                      "totalPaginas": math.ceil(total / tamanho)},
    }


@router.get("/ofertas/{id}", tags=["ofertas"])
def obter_oferta(id: UUID):
    with db.conexao() as conn:
        linha = conn.execute("SELECT * FROM oferta WHERE id = %s", (id,)).fetchone()
    if linha is None:
        raise _nao_encontrado("oferta")
    return _oferta(linha)
