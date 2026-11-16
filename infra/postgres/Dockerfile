# Imagem PostgreSQL do CampoConecta, usada pelas 4 instâncias
# (pg-editais, pg-ofertas, pg-compras, pg-entregas).
# Mesma imagem, 4 contêineres, 4 volumes e 4 redes: o isolamento está nos
# dados e na rede, não em ter imagens diferentes.
#
# Customização em relação à imagem oficial:
#  - script de inicialização que cria o usuário da aplicação (app_<serviço>),
#    sem superusuário, dono apenas do próprio banco (princípio do menor privilégio);
#  - parâmetros do servidor: limite de conexões, fuso e log de consultas lentas;
#  - healthcheck embutido (pg_isready).

FROM postgres:16-alpine

COPY --chmod=0755 init/01-usuario-aplicacao.sh /docker-entrypoint-initdb.d/

HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" || exit 1

CMD ["postgres", \
     "-c", "max_connections=50", \
     "-c", "timezone=America/Sao_Paulo", \
     "-c", "log_min_duration_statement=500", \
     "-c", "log_connections=on"]
