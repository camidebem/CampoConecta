# ADR 0005 — SAGA orquestrada por Compras para confirmar compra

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** equipe CampoConecta
- **Relacionados:** [`05-saga.md`](../parte2/05-saga.md), [`06-mensagens.md`](../parte2/06-mensagens.md), [`ADR 0001`](./0001-quatro-servicos-de-dominio.md), [`ADR 0004`](./0004-outbox-transacional.md)

## Contexto

Confirmar uma compra exige efeitos em quatro serviços, cada um com seu banco: Compras registra a compra, Editais reserva saldo do item do edital, Ofertas reserva a produção e Entregas reserva capacidade e agenda a entrega. Não existe transação de banco que atravesse serviços, e qualquer passo pode ser rejeitado (saldo, produção ou capacidade insuficientes) ou ficar sem resposta.

A homologação de um plano gera N compras. Cada uma precisa avançar, ser compensada ou ficar visível como pendente de forma independente, com timeouts, repetição segura e auditoria do que foi desfeito.

O enunciado exige **uma única variante** de SAGA, justificada frente à alternativa.

## Decisão

Adotamos **SAGA orquestrada**, com o orquestrador no serviço **Compras**:

- uma SAGA independente por Compra, iniciada pela homologação do plano;
- sequência fixa: `AlocarDemanda` (Editais) → `ReservarOferta` (Ofertas) → `AgendarEntrega` (Entregas) → conclusão em Compras;
- compensações em ordem inversa: `CancelarAgendamento`, `LiberarOferta`, `LiberarDemanda`;
- estado da SAGA persistido em Compras (`saga_compra`), atualizado na mesma transação local que grava o próximo comando no outbox;
- cada passo tem `operationId` próprio; participantes são idempotentes por `(compraId, operationId)`;
- timeout com resultado desconhecido gera **repetição do mesmo comando**, não falha presumida;
- a Compra só termina `CANCELADA` depois de todas as compensações confirmadas.

Os participantes respondem com eventos (`DemandaAlocada`, `OfertaReservada` etc.), mas quem decide o próximo passo é sempre o orquestrador. O uso de eventos não torna a SAGA coreografada.

## Alternativas consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| SAGA coreografada | O fluxo ficaria implícito nas assinaturas de eventos de cada serviço; timeouts, compensações e o estado global da compra teriam de ser reconstruídos a partir de quatro bancos; acrescentar ou reordenar um passo exigiria alterar vários participantes |
| Two-phase commit (2PC/XA) | Bloqueia recursos entre serviços, depende de coordenador e de suporte XA no broker; contradiz a autonomia de banco por serviço |
| Chamadas HTTP síncronas encadeadas | Falha parcial sem registro durável; acoplamento temporal entre os quatro serviços; sem retomada após reinício |
| Orquestrador como serviço separado | Mais um componente e banco sem regra de negócio própria; a compra e sua SAGA pertencem ao mesmo dono |

## Consequências

**Positivas:** fluxo explícito em um só lugar; estado consultável por compra (alimenta a projeção `AcompanhamentoCompra`); compensações auditáveis; retomada após reinício a partir do estado persistido; participantes simples, que só conhecem seus comandos.

**Negativas:** Compras concentra a lógica de coordenação e passa a depender da disponibilidade do broker; participantes precisam manter estado por operação para tratar respostas tardias; compensações que falham repetidamente exigem monitoramento e intervenção manual.

**Limite explícito:** recebimento e liberação de pagamento **não** fazem parte desta SAGA. São um fluxo posterior disparado por `EntregaRecebida`, e um cancelamento após a confirmação é outro processo de negócio.

## Referências

- `docs/parte2/05-saga.md`
- `docs/parte2/06-mensagens.md`
- `docs/parte2/00-base-comum.md`, seção 7
