# Decisões de arquitetura (ADRs)

Cada ADR registra **contexto**, **decisão**, **alternativas consideradas** e **consequências**. Uma decisão nova entra como arquivo numerado, não como edição de uma decisão anterior.

| ADR | Decisão | Status |
|---|---|---|
| [0001](0001-quatro-servicos-de-dominio.md) | Quatro serviços de domínio: Editais, Ofertas, Compras e Entregas | Aceito |
| [0002](0002-postgresql-por-servico.md) | PostgreSQL com uma instância por serviço | Aceito |
| [0003](0003-cqrs-em-compras.md) | CQRS em Compras com a projeção `AcompanhamentoCompra` | Aceito |
| [0004](0004-outbox-transacional.md) | Outbox transacional com inbox idempotente | Aceito |
| [0005](0005-saga-orquestrada.md) | SAGA orquestrada por Compras para confirmar compra | Aceito |

## Como registrar uma nova decisão

1. Criar `NNNN-titulo-curto.md` com o próximo número livre.
2. Preencher status, data, contexto, decisão, alternativas e consequências.
3. Atualizar a tabela acima.
4. Abrir PR — decisão que afeta outra frente é revisada por quem for afetado.
