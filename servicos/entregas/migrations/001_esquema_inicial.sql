CREATE TABLE capacidade_logistica (
    id             uuid PRIMARY KEY,
    escola_id      uuid NOT NULL,
    janela_inicio  timestamptz NOT NULL,
    janela_fim     timestamptz NOT NULL,
    capacidade_kg  numeric(14,2) NOT NULL CHECK (capacidade_kg > 0),
    reservado_kg   numeric(14,2) NOT NULL DEFAULT 0,
    versao         integer NOT NULL DEFAULT 1,
    CHECK (janela_inicio < janela_fim),
    CHECK (reservado_kg >= 0 AND reservado_kg <= capacidade_kg)
);
CREATE INDEX capacidade_escola_janela_idx ON capacidade_logistica (escola_id, janela_inicio, janela_fim);

CREATE TABLE idempotencia (
    chave       uuid NOT NULL,
    metodo      text NOT NULL,
    caminho     text NOT NULL,
    hash_corpo  text NOT NULL,
    status      integer,
    corpo       jsonb,
    location    text,
    criado_em   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (chave, metodo, caminho)
);
