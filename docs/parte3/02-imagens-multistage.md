# Imagens e multi-stage build

## Decisão

Os serviços Python usam **build em dois estágios** ([`servicos/editais/Dockerfile`](../../servicos/editais/Dockerfile)):

| Estágio | Base | O que contém | Vai para a imagem final? |
|---|---|---|---|
| `builder` | `python:3.12-slim` | `build-essential`, `libpq-dev`, pip, venv `/opt/venv` com as dependências compiladas | Só o diretório `/opt/venv` |
| `runtime` | `python:3.12-slim` | `libpq5`, `/opt/venv`, código e migrações, usuário `app` | Sim |

## Por que é aplicável aqui

O driver do PostgreSQL é o `psycopg[c]`, compilado contra a `libpq` do sistema. Compilar exige `gcc` e os headers da `libpq` (`libpq-dev`), mas **executar** exige só a biblioteca `libpq5`. Sem multi-stage, o compilador e os headers ficam na imagem que roda em produção.

Ganhos:

1. **Tamanho:** a imagem final não carrega toolchain, headers nem cache do pip (medição abaixo).
2. **Superfície de ataque:** não há `gcc` nem `pg_config` no contêiner em execução; menos pacotes, menos CVEs.
3. **Cache de build:** `requirements.txt` é copiado antes do código, então mudar o código não recompila as dependências.

Outras práticas da imagem: processo como usuário sem privilégio (`app`, uid 10001), `HEALTHCHECK` embutido usando o próprio Python (a imagem não tem `curl`), `CMD` em forma exec (o `uvicorn` recebe o `SIGTERM` do `docker stop` direto), `.dockerignore` para não enviar `__pycache__`, testes e `.env` no contexto.

## Medição

Comparação feita com [`Dockerfile.estagio-unico`](../../servicos/editais/Dockerfile.estagio-unico): mesmas dependências e mesmo resultado funcional, tudo em um estágio.

```bash
bash scripts/medir-imagens.sh
```

| Variante | Tamanho | `gcc` na imagem | `pg_config` na imagem |
|---|---|---|---|
| Estágio único | 736 MB | sim | sim |
| Multi-stage | 267 MB | não | não |
| **Redução** | **468 MB (63%)** | | |

> Medido em 16/11/2026, Docker 29.9.3 (Docker Desktop, backend WSL 2), Windows 11. Tamanho de `docker image inspect -f '{{.Size}}'`.

A maior parte da diferença é o `build-essential` (gcc, make, headers) e o `libpq-dev`, que no estágio único ficam na imagem final só porque foram necessários para compilar o `psycopg[c]`.

## PostgreSQL

As 4 instâncias usam uma única imagem customizada, [`infra/postgres/Dockerfile`](../../infra/postgres/Dockerfile), sobre `postgres:16-alpine`. Multi-stage não se aplica: nada é compilado. A customização está detalhada em [`03-bancos-e-persistencia.md`](./03-bancos-e-persistencia.md).
