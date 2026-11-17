"""Entradas do subconjunto de propostas definido na Parte 2."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Quantidade(Entrada):
    valor: str = Field(pattern=r"^(0\.(0[1-9]|[1-9][0-9])|[1-9][0-9]{0,11}\.[0-9]{2})$")
    unidade: str = Field(min_length=1, max_length=20)


class Dinheiro(Entrada):
    valor: str = Field(pattern=r"^(0|[1-9][0-9]{0,11})\.[0-9]{2}$")
    moeda: str = Field(pattern=r"^[A-Z]{3}$")


class PropostaCriacao(Entrada):
    editalId: UUID
    itemEditalId: UUID
    ofertaId: UUID
    quantidade: Quantidade
    precoUnitario: Dinheiro
