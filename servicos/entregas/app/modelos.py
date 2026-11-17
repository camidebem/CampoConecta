"""Entradas de capacidade logística do contrato da Parte 2."""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Janela(Entrada):
    inicio: AwareDatetime
    fim: AwareDatetime

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.inicio >= self.fim:
            raise ValueError("O início deve ser anterior ao fim da janela.")
        return self


class CapacidadeCriacao(Entrada):
    escolaId: UUID
    janela: Janela
    capacidadeKg: str = Field(pattern=r"^(0\.(0[1-9]|[1-9][0-9])|[1-9][0-9]{0,11}\.[0-9]{2})$")
