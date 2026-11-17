-- Referências externas são UUIDs, nunca FKs para bancos de outros serviços.
CREATE TABLE proposta (
    id              uuid PRIMARY KEY,
    edital_id       uuid NOT NULL,
    item_edital_id  uuid NOT NULL,
    oferta_id       uuid NOT NULL,
    produtor_id     uuid NOT NULL,
    quantidade      numeric(14,2) NOT NULL CHECK (quantidade > 0),
    unidade         text NOT NULL,
    preco_unitario  numeric(14,2) NOT NULL CHECK (preco_unitario >= 0),
    moeda           char(3) NOT NULL,
    status          text NOT NULL DEFAULT 'ENVIADA'
                    CHECK (status IN ('ENVIADA', 'ALOCADA', 'RETIRADA', 'REJEITADA')),
    snapshot        jsonb NOT NULL,
    criado_em       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX proposta_edital_idx ON proposta (edital_id);
CREATE INDEX proposta_produtor_idx ON proposta (produtor_id);

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
