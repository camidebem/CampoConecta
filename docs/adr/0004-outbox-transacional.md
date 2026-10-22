# ADR 0004 — Outbox transacional com inbox idempotente

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** equipe CampoConecta
- **Relacionados:** [`02-dados-outbox.md`](../parte2/02-dados-outbox.md)

## Contexto

Os serviços precisam confirmar a alteração no banco e avisar outros serviços. Publicar no broker logo após o `COMMIT` cria uma janela de falha: se o processo cair entre as duas operações, o dado existe no banco e o evento nunca é publicado (dual write). Transação distribuída (2PC) não é compatível com o modelo de banco por serviço adotado.

## Decisão

Adotamos **Transactional Outbox** como padrão único de publicação de comandos e eventos duráveis, combinado com **Idempotent Consumer (inbox)**:

1. A transação local grava a entidade **e** a linha do outbox.
2. Um relay publica as linhas pendentes e marca `published_at` após o *publisher confirm*.
3. O consumidor grava `message_id` na inbox e aplica os efeitos **na mesma transação**.
4. A unicidade de negócio (`compra_id`/`operation_id`, `UNIQUE compra_id` em `liberacao_pagamento`) é a segunda barreira contra duplicidade.

Escolhas associadas: *polling* de 500 ms com `FOR UPDATE SKIP LOCKED`, backoff exponencial com *jitter*, DLQ por serviço e retenção de 7 dias para linhas publicadas.

## Alternativas consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| Publicar direto no broker após o `COMMIT` | Janela de dual write; perda silenciosa de evento |
| 2PC / transação distribuída | Não escala, exige coordenação e não é suportada entre serviços isolados |
| CDC com Debezium | Viável, mas adiciona infraestrutura; o relay pode ser substituído por CDC depois sem mudar contrato |
| Tabela de eventos pesquisada pelo consumidor | Acoplamento e *polling* cruzado entre bancos |

## Consequências

**Positivas:** nenhum evento é perdido por falha entre banco e broker; reentrega é inofensiva; auditoria natural; mesmo padrão em todos os serviços.

**Negativas:** entrega é *at-least-once* (exige inbox); latência mínima de até um ciclo do relay; tabela cresce e precisa de rotina de limpeza; exige métrica de *lag* e DLQ.

## Referências

- `docs/parte2/02-dados-outbox.md`, seções 7 a 9
- `docs/parte2/00-base-comum.md`, seção 8.2
