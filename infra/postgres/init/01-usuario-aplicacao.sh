#!/bin/sh
# Executado pela imagem oficial SOMENTE na primeira inicialização
# (quando o volume de dados está vazio).
#
# Cria o usuário que o serviço usa (APP_DB_USER), sem superusuário,
# e o torna dono apenas do banco POSTGRES_DB. O superusuário (POSTGRES_USER)
# fica restrito à administração e não é usado pela aplicação.
set -eu

: "${APP_DB_USER:?defina APP_DB_USER}"
: "${APP_DB_PASSWORD:?defina APP_DB_PASSWORD}"

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v app_user="$APP_DB_USER" \
     -v app_password="$APP_DB_PASSWORD" \
     -v db="$POSTGRES_DB" <<'SQL'
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE CONNECTION LIMIT 20;

-- Dono do banco => dono do schema public (PostgreSQL 15+), pode criar as tabelas das migrações.
ALTER DATABASE :"db" OWNER TO :"app_user";

-- Ninguém além do dono (e do admin) se conecta a este banco.
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
SQL

echo "Usuário de aplicação '$APP_DB_USER' criado para o banco '$POSTGRES_DB'."
