# ADR 0002 — PostgreSQL com uma instância por serviço

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** equipe CampoConecta (frente de serviços e dados)
- **Relacionados:** [`02-dados-outbox.md`](../parte2/02-dados-outbox.md)

## Contexto

O enunciado exige **um banco por microsserviço, com instâncias separadas** e permite poliglotismo. As operações críticas são reservas concorrentes de saldo (edital, produção, capacidade) e publicação de eventos junto à transação local (outbox). Era necessário escolher a tecnologia e decidir se haveria diversidade de bancos.

## Decisão

Usamos **PostgreSQL, uma instância por serviço** (quatro instâncias), com usuário e credenciais próprios por serviço, sem superusuário e sem credenciais versionadas.

Fazemos o controle de concorrência das reservas por **`UPDATE` condicional** com `CHECK` de saldo não negativo, em `READ COMMITTED`.

## Alternativas consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| Quatro *schemas* em uma instância | Não atende ao requisito de instâncias separadas |
| Poliglotismo (ex.: MongoDB em um serviço) | Multiplicaria operação e não resolve nenhum problema do domínio |
| Banco compartilhado | Quebra autonomia e recria acoplamento por dados |
| Controle de concorrência por advisory lock global | Serializa demais e não é necessário: o `UPDATE` condicional já é atômico |

## Consequências

**Positivas:** transações ACID para reservas e outbox; constraints impedem saldo negativo no nível do banco; `jsonb` para critérios do edital; operação uniforme; um único padrão de migração e de backup.

**Negativas:** sem `JOIN` entre serviços (resolvido por snapshots e CQRS); o poliglotismo exigido como opcional não é exercitado — decisão consciente e justificada.

## Referências

- `docs/parte2/00-base-comum.md`, seção 8
- `docs/parte2/02-dados-outbox.md`, seções 2, 5 e 7
