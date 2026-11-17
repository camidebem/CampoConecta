-- Serviço Editais — esquema inicial (modelo de dados em docs/parte2/02-dados-outbox.md, seção 3.1).
-- Chaves estrangeiras só entre tabelas DESTE banco; nenhuma referência a outros serviços.

CREATE TABLE prefeitura (
    id          uuid PRIMARY KEY,
    nome        text        NOT NULL,
    cnpj        char(14)    NOT NULL UNIQUE,
    criado_em   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE escola (
    id             uuid PRIMARY KEY,
    prefeitura_id  uuid        NOT NULL REFERENCES prefeitura (id),
    nome           text        NOT NULL,
    endereco       jsonb       NOT NULL,
    ativo          boolean     NOT NULL DEFAULT true,
    criado_em      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX escola_prefeitura_idx ON escola (prefeitura_id);

CREATE TABLE edital (
    id             uuid PRIMARY KEY,
    prefeitura_id  uuid        NOT NULL REFERENCES prefeitura (id),
    titulo         text        NOT NULL,
    status         text        NOT NULL DEFAULT 'RASCUNHO'
                   CHECK (status IN ('RASCUNHO', 'PUBLICADO', 'ENCERRADO')),
    prazo_entrega  timestamptz NOT NULL,
    criterios      jsonb       NOT NULL,  -- lista ordenada de critérios: dado, não código
    versao         integer     NOT NULL DEFAULT 1,
    criado_em      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX edital_status_idx ON edital (status, criado_em DESC);
CREATE INDEX edital_prefeitura_idx ON edital (prefeitura_id);

CREATE TABLE item_edital (
    id          uuid PRIMARY KEY,
    edital_id   uuid          NOT NULL REFERENCES edital (id) ON DELETE CASCADE,
    escola_id   uuid          NOT NULL REFERENCES escola (id),
    produto     text          NOT NULL,
    unidade     text          NOT NULL,
    quantidade  numeric(14,2) NOT NULL CHECK (quantidade > 0),
    saldo       numeric(14,2) NOT NULL,
    versao      integer       NOT NULL DEFAULT 1,
    -- O banco impede saldo negativo mesmo sob concorrência (UPDATE condicional na SAGA).
    CONSTRAINT item_edital_saldo_valido CHECK (saldo >= 0 AND saldo <= quantidade)
);
CREATE INDEX item_edital_edital_idx ON item_edital (edital_id);
CREATE INDEX item_edital_produto_idx ON item_edital (produto);

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
