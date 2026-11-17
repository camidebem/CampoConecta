# Modelo base dos serviços (Python + FastAPI)

Todo app Python do CampoConecta (serviços de domínio, BFFs e `authn-verify`) segue o mesmo modelo. A referência é [`servicos/editais`](../../servicos/editais).

## Estrutura

```
servicos/<nome>/
├── Dockerfile               multi-stage (builder + runtime)
├── .dockerignore
├── requirements.txt         versões fixadas
├── migrations/
│   └── 001_esquema_inicial.sql
└── app/
    ├── main.py              FastAPI, /health, X-Correlation-Id, lifespan (migra + abre pool)
    ├── config.py            lê só variáveis de ambiente
    ├── db.py                pool de conexões psycopg (limite explícito)
    ├── migracoes.py         aplica migrations/*.sql uma vez, com advisory lock
    ├── erros.py             formato único de erro {code, message, details, correlationId}
    ├── idempotencia.py      Idempotency-Key nos POST
    ├── modelos.py           validação de entrada (Pydantic, campos extras recusados)
    └── rotas.py             endpoints /api/v1/...
```

`config.py`, `db.py`, `migracoes.py`, `erros.py` e `idempotencia.py` são iguais em todos os serviços. Eles ficam **copiados** em cada serviço e não numa biblioteca compartilhada: cada serviço builda e evolui sem depender dos outros.

## Combinados

| Item | Valor |
|---|---|
| Imagem base | `python:3.12-slim` nos dois estágios |
| Porta interna | `8000` (nenhum serviço publica porta; só o gateway) |
| Saúde | `GET /health` → `200` se o banco responde, `503` se não |
| Rotas de domínio | `/api/v1/...`, seguindo `docs/parte2/openapi/<serviço>.openapi.json` |
| Hostname | nome do serviço no compose (`editais`, `ofertas`, `compras`, `entregas`, `pg-<serviço>`, ...) |
| Configuração | só por ambiente: `DATABASE_URL`, `SERVICE_NAME`, `DB_POOL_MAX`, `LOG_LEVEL` (e `RABBITMQ_URL`, `JWT_SECRET` onde couber) |
| Usuário do processo | `app` (uid 10001), sem root |
| Swagger | `/docs` em cada serviço (útil para testar antes do gateway) |

## Como criar um novo serviço a partir do modelo

1. Copie `servicos/editais` para `servicos/<nome>`.
2. No `Dockerfile`, troque `SERVICE_NAME=editais`.
3. Em `app/migracoes.py`, use outro `CHAVE_LOCK` (só por clareza; cada banco é separado).
4. Reescreva `migrations/001_esquema_inicial.sql`, `app/modelos.py` e `app/rotas.py` com o seu domínio. Mantenha a tabela `idempotencia`.
5. No `docker-compose.yml`, adicione o serviço com `DATABASE_URL` apontando para `pg-<nome>` e as redes `[aplicacao, dados-<nome>]`.

## Endpoints já implementados

| Serviço | Endpoints |
|---|---|
| Editais | `POST/GET /prefeituras`, `POST/GET /escolas`, `POST /editais`, `GET /editais` (paginado, filtros `status`, `prefeituraId`, `produto`), `GET /editais/{id}` |
| Ofertas | `POST/GET /produtores`, `POST /ofertas`, `GET /ofertas` (paginado, filtros `ativa`, `produto`), `GET /ofertas/{id}` |
| Compras | `POST /propostas`, `GET /propostas/{id}`; validação de referências via HTTP e snapshot histórico |
| Entregas | `POST /capacidades`, `GET /capacidades/{id}`; validação de janelas e proteção contra sobreposição |

Todos os `POST` exigem `Idempotency-Key` (UUID). Reenvio igual devolve a resposta original com `Idempotent-Replayed: true`; mesma chave com outro corpo devolve `409`.

Compras também usa `EDITAIS_URL`, `OFERTAS_URL` e `HTTP_TIMEOUT` (segundos) para consultas internas. A configuração HTTP fica em `app/dependencias.py`. Os quatro serviços participam de `mensageria`, além de `aplicacao` e da própria rede de dados; o `RABBITMQ_URL` recebido por ambiente será consumido na Parte 4.

## Fora do escopo desta etapa

- Validação do JWT dentro do serviço: nesta etapa a autenticação fica na borda (gateway + `authn-verify`), e os serviços só são alcançáveis pela rede `aplicacao`.
- Outbox, relay e consumidores RabbitMQ: entram com a SAGA na Parte 4, em novas migrações (`002_...sql`).
