# syntax=docker/dockerfile:1
# Modelo base dos serviços Python do CampoConecta (multi-stage).
#
# Estágio 1 (builder): tem compilador e headers da libpq para compilar as
# dependências (psycopg[c]) dentro de um virtualenv em /opt/venv.
# Estágio 2 (runtime): parte de uma imagem slim limpa e recebe só o virtualenv
# pronto + o código. Compilador, headers, cache do pip e camadas de apt do
# builder não vão para a imagem final. Ganho medido em docs/parte3/02-imagens-multistage.md.

ARG PYTHON_VERSION=3.12

# ---------- estágio 1: build das dependências ----------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Copiar só o requirements primeiro: enquanto ele não mudar, esta camada
# (a mais lenta) vem do cache, mesmo que o código mude.
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- estágio 2: imagem final ----------
FROM python:${PYTHON_VERSION}-slim AS runtime

# libpq5 é a biblioteca de execução exigida pelo psycopg compilado.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home app

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME=editais

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY migrations ./migrations

# Processo sem privilégio de root.
USER app

EXPOSE 8000

# Usa o próprio Python (a imagem não tem curl). /health responde 200 só se o banco responde.
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
