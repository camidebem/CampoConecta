# ADR 0003 — CQRS em Compras com a projeção AcompanhamentoCompra

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** equipe CampoConecta
- **Relacionados:** [`03-cqrs.md`](../parte2/03-cqrs.md), [`ADR 0001`](./0001-quatro-servicos-de-dominio.md)

## Contexto

Com banco por serviço, o acompanhamento de uma compra combina dados de quatro serviços (Compras, Editais, Ofertas e Entregas) mais o progresso da SAGA. Sem projeção, cada leitura exigiria quatro chamadas HTTP em série e reconstrução do estado no cliente.

## Decisão

Aplicamos **CQRS em Compras**, com:

- modelo de escrita normalizado (fonte de verdade);
- tabela de leitura `acompanhamento_compra`, na mesma instância, atualizada por eventos via outbox/inbox;
- ordem por `aggregate_version`, descartando evento mais antigo que a versão armazenada;
- meta de defasagem de **até 5 segundos**, declarada como meta ainda não medida;
- **reconstrução a partir das tabelas de escrita**, sem depender de replay do broker.

## Alternativas consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| Agregação no BFF (4 chamadas) | Latência em série, falha em cascata, lógica no cliente |
| Projeção em banco separado | Custo operacional sem benefício; separação lógica já permite reconstruir |
| Event sourcing completo | Reescreveria o modelo de escrita; a projeção resolve a leitura |
| `VIEW` materializada | Não atravessa bancos |
| Cache de resposta no BFF | Não resolve composição nem ordenação |

## Consequências

**Positivas:** leitura em uma consulta; BFFs simples; escrita protegida por invariantes; projeção reconstruível e idempotente.

**Negativas:** defasagem eventual de até 5 s; necessidade de projetor, inbox e métrica de *lag*; mais uma tabela a manter.

**Limite explícito:** a projeção **não** decide saldo, autorização ou pagamento. Decisão crítica sempre consulta o serviço dono.

## Referências

- `docs/parte2/03-cqrs.md`
- `docs/parte2/00-base-comum.md`, seção 8.3
