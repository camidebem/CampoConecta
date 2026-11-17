"""Configuração lida apenas de variáveis de ambiente (nada fixo no código)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    servico: str
    database_url: str
    pool_min: int
    pool_max: int
    log_level: str


def carregar() -> Config:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Variável de ambiente DATABASE_URL não definida.")
    return Config(
        servico=os.environ.get("SERVICE_NAME", "servico"),
        database_url=database_url,
        pool_min=int(os.environ.get("DB_POOL_MIN", "1")),
        pool_max=int(os.environ.get("DB_POOL_MAX", "5")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
