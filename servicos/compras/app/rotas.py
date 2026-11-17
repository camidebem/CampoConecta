"""Criação e consulta de propostas; homologação/SAGA ficam para a Parte 4."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, Request
from psycopg.types.json import Jsonb

from . import db, dependencias, idempotencia
from .erros import ErroApi
from .idempotencia import Resultado
from .modelos import PropostaCriacao

router = APIRouter()


def _proposta(linha: dict) -> dict:
    return {
        "id": str(linha["id"]),
        "editalId": str(linha["edital_id"]),
        "itemEditalId": str(linha["item_edital_id"]),
        "ofertaId": str(linha["oferta_id"]),
        "produtorId": str(linha["produtor_id"]),
        "quantidade": {"valor": format(linha["quantidade"], ".2f"), "unidade": linha["unidade"]},
        "precoUnitario": {"valor": format(linha["preco_unitario"], ".2f"), "moeda": linha["moeda"]},
        "status": linha["status"],
        "snapshot": linha["snapshot"],
        "criadoEm": linha["criado_em"].isoformat(),
    }


def _validar_referencias(dados: PropostaCriacao, request: Request) -> tuple[UUID, dict]:
    edital = dependencias.consultar("editais", f"editais/{dados.editalId}", request)
    oferta = dependencias.consultar("ofertas", f"ofertas/{dados.ofertaId}", request)
    try:
        if edital["status"] != "PUBLICADO":
            raise ErroApi(409, "EDITAL_NAO_PUBLICADO", "O edital precisa estar publicado.")
        item = next((i for i in edital["itens"] if i["id"] == str(dados.itemEditalId)), None)
        if item is None:
            raise ErroApi(404, "ITEM_NAO_ENCONTRADO", "Item não encontrado no edital.")
        if not oferta["ativa"]:
            raise ErroApi(409, "OFERTA_INATIVA", "A oferta precisa estar ativa.")
        if (item["produto"] != oferta["produto"] or
                dados.quantidade.unidade != item["quantidade"]["unidade"] or
                dados.quantidade.unidade != oferta["quantidadeDisponivel"]["unidade"]):
            raise ErroApi(409, "PRODUTO_UNIDADE_INCOMPATIVEL", "Produto ou unidade incompatível.")

        # Na Parte 3, ainda sem autorização por recurso, a identidade do produtor
        # vem da oferta autoritativa. Não é aceita como campo livre do corpo.
        produtor_id = UUID(oferta["produtorId"])
        produtor = dependencias.consultar("ofertas", f"produtores/{produtor_id}", request)
        escola = dependencias.consultar("editais", f"escolas/{item['escolaId']}", request)
        if not produtor["ativo"] or not escola["ativo"]:
            raise ErroApi(409, "CADASTRO_INATIVO", "Produtor e escola precisam estar ativos.")
        snapshot = {
            "editalTitulo": edital["titulo"], "escolaId": item["escolaId"],
            "escolaNome": escola["nome"], "produtorNome": produtor["nome"],
            "produto": item["produto"], "snapshotAt": datetime.now(timezone.utc).isoformat(),
        }
        return produtor_id, snapshot
    except (KeyError, TypeError, ValueError) as exc:
        raise ErroApi(503, "RESPOSTA_DEPENDENCIA_INVALIDA",
                      "Uma dependência retornou dados incompatíveis.") from exc


@router.post("/propostas", status_code=201, tags=["propostas"])
def criar_proposta(dados: PropostaCriacao, request: Request,
                   idempotency_key: UUID = Header(alias="Idempotency-Key")):
    def acao(conn):
        produtor_id, snapshot = _validar_referencias(dados, request)
        linha = conn.execute(
            "INSERT INTO proposta (id, edital_id, item_edital_id, oferta_id, produtor_id,"
            " quantidade, unidade, preco_unitario, moeda, snapshot)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *",
            (uuid.uuid4(), dados.editalId, dados.itemEditalId, dados.ofertaId, produtor_id,
             Decimal(dados.quantidade.valor), dados.quantidade.unidade,
             Decimal(dados.precoUnitario.valor), dados.precoUnitario.moeda, Jsonb(snapshot)),
        ).fetchone()
        return Resultado(201, _proposta(linha), f"/api/v1/propostas/{linha['id']}")

    return idempotencia.executar(request, idempotency_key, dados.model_dump(mode="json"), acao)


@router.get("/propostas/{id}", tags=["propostas"])
def obter_proposta(id: UUID):
    with db.conexao() as conn:
        linha = conn.execute("SELECT * FROM proposta WHERE id = %s", (id,)).fetchone()
    if linha is None:
        raise ErroApi(404, "PROPOSTA_NAO_ENCONTRADA", "Proposta não encontrada.")
    return _proposta(linha)
