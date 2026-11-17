"""Modelos de entrada (validação), espelhando docs/parte2/openapi/editais.openapi.json.

Campos desconhecidos são recusados (additionalProperties: false no contrato).
"""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

Texto200 = Annotated[str, StringConstraints(min_length=1, max_length=200)]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Quantidade(Entrada):
    # Decimal exato, estritamente positivo, duas casas, transmitido como string (nunca float).
    valor: str = Field(pattern=r"^(0\.(0[1-9]|[1-9][0-9])|[1-9][0-9]{0,11}\.[0-9]{2})$")
    unidade: str = Field(min_length=1, max_length=20)


class PrefeituraCriacao(Entrada):
    nome: Texto200
    cnpj: str = Field(pattern=r"^[0-9]{14}$")


class Endereco(Entrada):
    logradouro: Texto200
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, min_length=1, max_length=100)
    bairro: Texto200
    municipio: Texto200
    uf: str = Field(pattern=r"^[A-Z]{2}$")
    cep: str = Field(pattern=r"^[0-9]{8}$")


class EscolaCriacao(Entrada):
    prefeituraId: UUID
    nome: Texto200
    endereco: Endereco


class CriterioAlocacao(Entrada):
    codigo: Literal["ORDEM_ENVIO", "PRECO_UNITARIO"]
    ordem: Literal["ASC", "DESC"]
    parametros: dict = Field(max_length=0)  # obrigatório e vazio nestas estratégias


class ItemEditalCriacao(Entrada):
    escolaId: UUID
    produto: Texto200
    quantidade: Quantidade


class EditalCriacao(Entrada):
    prefeituraId: UUID
    titulo: Texto200
    prazoEntrega: AwareDatetime  # exige fuso horário
    criterios: list[CriterioAlocacao] = Field(min_length=1)
    itens: list[ItemEditalCriacao] = Field(min_length=1)
