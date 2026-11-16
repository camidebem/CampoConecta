"""Endpoints do serviço Editais (subconjunto do contrato da Parte 2).

POST /prefeituras        GET /prefeituras/{id}
POST /escolas            GET /escolas/{id}
POST /editais            GET /editais            GET /editais/{id}
"""

import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from psycopg import errors as pg_errors
from psycopg.types.json import Jsonb

from . import db, idempotencia
from .erros import ErroApi
from .idempotencia import Resultado
from .modelos import EditalCriacao, EscolaCriacao, PrefeituraCriacao

router = APIRouter()


# ---------- serialização (banco -> contrato) ----------

def _decimal(v: Decimal) -> str:
    return format(v, ".2f")


def _data(v: datetime) -> str:
    return v.isoformat()


def _prefeitura(l: dict) -> dict:
    return {"id": str(l["id"]), "nome": l["nome"], "cnpj": l["cnpj"], "criadoEm": _data(l["criado_em"])}


def _escola(l: dict) -> dict:
    return {"id": str(l["id"]), "prefeituraId": str(l["prefeitura_id"]), "nome": l["nome"],
            "endereco": l["endereco"], "ativo": l["ativo"]}


def _item(l: dict) -> dict:
    return {
        "id": str(l["id"]),
        "escolaId": str(l["escola_id"]),
        "produto": l["produto"],
        "quantidade": {"valor": _decimal(l["quantidade"]), "unidade": l["unidade"]},
        "saldo": {"valor": _decimal(l["saldo"]), "unidade": l["unidade"]},
        "versao": l["versao"],
    }


def _edital(l: dict, itens: list[dict]) -> dict:
    return {
        "id": str(l["id"]),
        "prefeituraId": str(l["prefeitura_id"]),
        "titulo": l["titulo"],
        "prazoEntrega": _data(l["prazo_entrega"]),
        "criterios": l["criterios"],
        "itens": [_item(i) for i in itens],
        "status": l["status"],
        "versao": l["versao"],
    }


_NAO_ENCONTRADO = {
    "prefeitura": ("PREFEITURA_NAO_ENCONTRADA", "Prefeitura não encontrada."),
    "escola": ("ESCOLA_NAO_ENCONTRADA", "Escola não encontrada."),
    "edital": ("EDITAL_NAO_ENCONTRADO", "Edital não encontrado."),
}


def _nao_encontrado(recurso: str) -> ErroApi:
    return ErroApi(404, *_NAO_ENCONTRADO[recurso])


# ---------- prefeituras ----------

@router.post("/prefeituras", status_code=201, tags=["prefeituras"])
def criar_prefeitura(dados: PrefeituraCriacao, request: Request,
                     idempotency_key: UUID = Header(alias="Idempotency-Key")):
    def acao(conn):
        try:
            linha = conn.execute(
                "INSERT INTO prefeitura (id, nome, cnpj) VALUES (%s, %s, %s) RETURNING *",
                (uuid.uuid4(), dados.nome, dados.cnpj),
            ).fetchone()
        except pg_errors.UniqueViolation:
            raise ErroApi(409, "CNPJ_JA_CADASTRADO", "Já existe prefeitura com este CNPJ.",
                          [{"campo": "cnpj", "motivo": "duplicado"}])
        return Resultado(201, _prefeitura(linha), f"/api/v1/prefeituras/{linha['id']}")

    return idempotencia.executar(request, idempotency_key, dados.model_dump(mode="json"), acao)


@router.get("/prefeituras/{id}", tags=["prefeituras"])
def obter_prefeitura(id: UUID):
    with db.conexao() as conn:
        linha = conn.execute("SELECT * FROM prefeitura WHERE id = %s", (id,)).fetchone()
    if linha is None:
        raise _nao_encontrado("prefeitura")
    return _prefeitura(linha)


# ---------- escolas ----------

@router.post("/escolas", status_code=201, tags=["escolas"])
def criar_escola(dados: EscolaCriacao, request: Request,
                 idempotency_key: UUID = Header(alias="Idempotency-Key")):
    def acao(conn):
        existe = conn.execute("SELECT 1 FROM prefeitura WHERE id = %s", (dados.prefeituraId,)).fetchone()
        if existe is None:
            raise _nao_encontrado("prefeitura")
        linha = conn.execute(
            "INSERT INTO escola (id, prefeitura_id, nome, endereco) VALUES (%s, %s, %s, %s) RETURNING *",
            (uuid.uuid4(), dados.prefeituraId, dados.nome, Jsonb(dados.endereco.model_dump(exclude_none=True))),
        ).fetchone()
        return Resultado(201, _escola(linha), f"/api/v1/escolas/{linha['id']}")

    return idempotencia.executar(request, idempotency_key, dados.model_dump(mode="json"), acao)


@router.get("/escolas/{id}", tags=["escolas"])
def obter_escola(id: UUID):
    with db.conexao() as conn:
        linha = conn.execute("SELECT * FROM escola WHERE id = %s", (id,)).fetchone()
    if linha is None:
        raise _nao_encontrado("escola")
    return _escola(linha)


# ---------- editais ----------

@router.post("/editais", status_code=201, tags=["editais"])
def criar_edital(dados: EditalCriacao, request: Request,
                 idempotency_key: UUID = Header(alias="Idempotency-Key")):
    # Regras de validação do contrato (400).
    detalhes = []
    if dados.prazoEntrega <= datetime.now(timezone.utc):
        detalhes.append({"campo": "prazoEntrega", "motivo": "deve ser uma data futura"})
    codigos = [c.codigo for c in dados.criterios]
    if len(codigos) != len(set(codigos)):
        detalhes.append({"campo": "criterios", "motivo": "códigos de critério repetidos"})
    if detalhes:
        raise ErroApi(400, "REQUISICAO_INVALIDA", "Dados da requisição inválidos.", detalhes)

    def acao(conn):
        if conn.execute("SELECT 1 FROM prefeitura WHERE id = %s", (dados.prefeituraId,)).fetchone() is None:
            raise _nao_encontrado("prefeitura")

        # Todas as escolas devem existir E pertencer à prefeitura do edital.
        # Escola de outra prefeitura recebe o mesmo 404, para não revelar dados de outro município.
        escolas_pedidas = {i.escolaId for i in dados.itens}
        validas = {
            l["id"] for l in conn.execute(
                "SELECT id FROM escola WHERE prefeitura_id = %s AND id = ANY(%s)",
                (dados.prefeituraId, list(escolas_pedidas)),
            )
        }
        faltando = escolas_pedidas - validas
        if faltando:
            raise ErroApi(404, "ESCOLA_NAO_ENCONTRADA", "Escola não encontrada nesta prefeitura.",
                          [{"campo": "itens.escolaId", "motivo": str(e)} for e in sorted(faltando, key=str)])

        edital_id = uuid.uuid4()
        edital = conn.execute(
            "INSERT INTO edital (id, prefeitura_id, titulo, prazo_entrega, criterios)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (edital_id, dados.prefeituraId, dados.titulo, dados.prazoEntrega,
             Jsonb([c.model_dump() for c in dados.criterios])),
        ).fetchone()
        itens = []
        for item in dados.itens:
            # Saldo inicial = quantidade demandada; a SAGA reserva sobre o saldo.
            itens.append(conn.execute(
                "INSERT INTO item_edital (id, edital_id, escola_id, produto, unidade, quantidade, saldo)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
                (uuid.uuid4(), edital_id, item.escolaId, item.produto, item.quantidade.unidade,
                 Decimal(item.quantidade.valor), Decimal(item.quantidade.valor)),
            ).fetchone())
        return Resultado(201, _edital(edital, itens), f"/api/v1/editais/{edital_id}")

    return idempotencia.executar(request, idempotency_key, dados.model_dump(mode="json"), acao)


@router.get("/editais", tags=["editais"])
def listar_editais(
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=50),
    status: Literal["RASCUNHO", "PUBLICADO", "ENCERRADO"] | None = None,
    prefeituraId: UUID | None = None,
    produto: str | None = Query(None, min_length=1, max_length=200),
):
    filtros, params = [], []
    if status:
        filtros.append("e.status = %s")
        params.append(status)
    if prefeituraId:
        filtros.append("e.prefeitura_id = %s")
        params.append(prefeituraId)
    if produto:
        filtros.append("EXISTS (SELECT 1 FROM item_edital i WHERE i.edital_id = e.id AND i.produto = %s)")
        params.append(produto)
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    with db.conexao() as conn:
        total = conn.execute(f"SELECT count(*) AS n FROM edital e {where}", params).fetchone()["n"]
        editais = conn.execute(
            f"SELECT * FROM edital e {where} ORDER BY e.criado_em DESC, e.id LIMIT %s OFFSET %s",
            [*params, tamanho, (pagina - 1) * tamanho],
        ).fetchall()
        itens_por_edital: dict = {e["id"]: [] for e in editais}
        if editais:
            for item in conn.execute(
                "SELECT * FROM item_edital WHERE edital_id = ANY(%s) ORDER BY produto, id",
                (list(itens_por_edital),),
            ):
                itens_por_edital[item["edital_id"]].append(item)

    return {
        "items": [_edital(e, itens_por_edital[e["id"]]) for e in editais],
        "paginacao": {"pagina": pagina, "tamanho": tamanho, "total": total,
                      "totalPaginas": math.ceil(total / tamanho)},
    }


@router.get("/editais/{id}", tags=["editais"])
def obter_edital(id: UUID):
    with db.conexao() as conn:
        edital = conn.execute("SELECT * FROM edital WHERE id = %s", (id,)).fetchone()
        if edital is None:
            raise _nao_encontrado("edital")
        itens = conn.execute(
            "SELECT * FROM item_edital WHERE edital_id = %s ORDER BY produto, id", (id,)
        ).fetchall()
    return _edital(edital, itens)
