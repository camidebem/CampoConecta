"""Pool de conexões com o PostgreSQL do próprio serviço.

Uso:  with db.conexao() as conn: conn.execute(...)
Ao sair do bloco sem exceção, a transação é confirmada; com exceção, é desfeita.
"""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import Config

_pool: ConnectionPool | None = None


def abrir(config: Config) -> None:
    global _pool
    _pool = ConnectionPool(
        conninfo=config.database_url,
        min_size=config.pool_min,
        max_size=config.pool_max,  # limite explícito: um serviço não esgota o banco
        kwargs={"row_factory": dict_row, "application_name": config.servico},
        timeout=5,
        open=False,
        name=config.servico,
    )
    # wait=False: o processo sobe mesmo com o banco fora; /health devolve 503.
    _pool.open(wait=False)


def fechar() -> None:
    if _pool is not None:
        _pool.close()


def conexao(timeout: float | None = None):
    if _pool is None:
        raise RuntimeError("Pool de conexões não inicializado.")
    return _pool.connection(timeout=timeout)
