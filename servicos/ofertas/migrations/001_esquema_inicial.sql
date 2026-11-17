-- Serviço Ofertas — esquema inicial (modelo de dados em docs/parte2/02-dados-outbox.md, seção 3.2).

CREATE TABLE produtor (
    id          uuid PRIMARY KEY,
    nome        text        NOT NULL,
    documento   varchar(14) NOT NULL UNIQUE,  -- CPF (11) ou CNPJ (14), sem pontuação
    email       text        NOT NULL,
    ativo       boolean     NOT NULL DEFAULT true,
    versao      integer     NOT NULL DEFAULT 1,
    criado_em   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE oferta (
    id                     uuid PRIMARY KEY,
    produtor_id            uuid          NOT NULL REFERENCES produtor (id),
    produto                text          NOT NULL,
    unidade                text          NOT NULL,
    quantidade_disponivel  numeric(14,2) NOT NULL,
    ativa                  boolean       NOT NULL DEFAULT true,
    versao                 integer       NOT NULL DEFAULT 1,
    criado_em              timestamptz   NOT NULL DEFAULT now(),
    -- O banco impede produção reservada além do disponível (UPDATE condicional na SAGA).
    CONSTRAINT oferta_quantidade_nao_negativa CHECK (quantidade_disponivel >= 0)
);
CREATE INDEX oferta_produtor_idx ON oferta (produtor_id);
CREATE INDEX oferta_produto_idx ON oferta (produto) WHERE ativa;

-- Respostas registradas por Idempotency-Key (ver app/idempotencia.py).
CREATE TABLE idempotencia (
    chave       uuid        NOT NULL,
    metodo      text        NOT NULL,
    caminho     text        NOT NULL,
    hash_corpo  text        NOT NULL,
    status      integer,
    corpo       jsonb,
    location    text,
    criado_em   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (chave, metodo, caminho)
);
