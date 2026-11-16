"""Aplica os arquivos migrations/*.sql em ordem, uma única vez cada.

- A tabela schema_migracoes registra o que já foi aplicado.
- pg_advisory_lock garante que, com várias réplicas subindo juntas
  (docker compose --scale), só uma aplica as migrações; as outras esperam.
- Enquanto o banco ainda não aceita conexões, tenta de novo com intervalo.
"""

import logging
import time
from pathlib import Path

import psycopg

log = logging.getLogger(__name__)

PASTA = Path(__file__).resolve().parent.parent / "migrations"
CHAVE_LOCK = 72_000_002  # identificador arbitrário do lock de migração


def aplicar(database_url: str, tentativas: int = 30, espera_s: float = 2.0) -> None:
    for tentativa in range(1, tentativas + 1):
        try:
            with psycopg.connect(database_url, autocommit=True, connect_timeout=5) as conn:
                _aplicar_pendentes(conn)
            return
        except psycopg.OperationalError as exc:
            log.warning("Banco indisponível (tentativa %d/%d): %s", tentativa, tentativas, exc)
            time.sleep(espera_s)
    raise RuntimeError("Não foi possível conectar ao banco para aplicar as migrações.")


def _aplicar_pendentes(conn: psycopg.Connection) -> None:
    conn.execute("SELECT pg_advisory_lock(%s::bigint)", (CHAVE_LOCK,))
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migracoes ("
            " versao text PRIMARY KEY,"
            " aplicada_em timestamptz NOT NULL DEFAULT now())"
        )
        aplicadas = {linha[0] for linha in conn.execute("SELECT versao FROM schema_migracoes")}
        for arquivo in sorted(PASTA.glob("*.sql")):
            if arquivo.name in aplicadas:
                continue
            with conn.transaction():
                conn.execute(arquivo.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migracoes (versao) VALUES (%s)", (arquivo.name,))
            log.info("Migração aplicada: %s", arquivo.name)
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s::bigint)", (CHAVE_LOCK,))
