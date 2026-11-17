"""Modelos de entrada (validação), espelhando docs/parte2/openapi/ofertas.openapi.json.

Campos desconhecidos são recusados (additionalProperties: false no contrato).
"""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

Texto200 = Annotated[str, StringConstraints(min_length=1, max_length=200)]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Quantidade(Entrada):
    # Decimal exato, estritamente positivo, duas casas, transmitido como string (nunca float).
    valor: str = Field(pattern=r"^(0\.(0[1-9]|[1-9][0-9])|[1-9][0-9]{0,11}\.[0-9]{2})$")
    unidade: str = Field(min_length=1, max_length=20)


class ProdutorCriacao(Entrada):
    nome: Texto200
    documento: str = Field(pattern=r"^([0-9]{11}|[0-9]{14})$")
    email: EmailStr  # email-validator já limita a 254 caracteres


class OfertaCriacao(Entrada):
    produtorId: UUID
    produto: Texto200
    quantidadeDisponivel: Quantidade
