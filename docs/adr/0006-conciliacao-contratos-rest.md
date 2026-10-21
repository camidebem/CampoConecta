# ADR 0006 — Contratos REST e regras de domínio

- **Status:** proposto.
- **Data:** 2026-10-20.
- **Componentes afetados:** Editais, Ofertas, Compras, Entregas e os dois BFFs.
- **Relacionados:** [contratos REST](../parte2/openapi/README.md).

## Contexto

Os contratos precisam representar escola de destino, valores monetários, critérios de alocação, vínculos de autorização e transições de estado de forma consistente entre serviços. Essas definições orientam a implementação e a integração dos clientes.

## Decisões propostas

| Tema | Definição proposta | Regra de integração |
|---|---|---|
| Escola do item | Cada item do edital inclui `escolaId` | Editais persiste e valida localmente o vínculo escola–prefeitura; o agendamento recebe a escola de destino |
| Valores monetários | `precoUnitario {valor, moeda}` na proposta e na compra; `valorTotal` calculado em Compras | Quantidade × preço unitário com decimal exato e arredondamento HALF_UP para duas casas. Uma moeda por edital/plano. A liberação usa o total da compra; Ofertas não controla preço |
| Critérios | `ORDEM_ENVIO` e `PRECO_UNITARIO`, com direção `ASC`/`DESC` e `parametros: {}` | Ordenação determinística; desempate pelo UUID da proposta em ordem lexical ascendente. Novos critérios exigem atualização coordenada dos contratos e do algoritmo |
| Autorização institucional | Vínculos autoritativos entre recursos, prefeitura, escola e produtor | Entregas precisa de provisionamento interno confiável do vínculo escola–prefeitura e do vínculo com o produtor. Snapshots de nomes e campos livres do cliente não concedem permissão |
| Homologação | Uma transação local grava plano, compras, SAGAs e outbox antes do `202` | Reservas e agendamento são posteriores, por comandos da SAGA. A falha de uma compra não desfaz as demais |
| Limite por proposta | Soma das quantidades homologadas não excede a quantidade proposta, inclusive entre planos | Unicidade por item do plano impede compras duplicadas. A proposta conta alocações homologadas mesmo após cancelamento; eventual realocação exige fluxo definido |
| Representação JSON | `updatedAt`, `etapaSaga` e `compraId` externamente; nomes físicos podem usar snake_case | Mapeamento explícito sem renomear tabelas. BFFs consultam a API de Compras, nunca a projeção por SQL |
| Concorrência | `versao` obrigatório nos ajustes e transições editáveis; conflito `409` | Reservas e liberações também incrementam a versão. `If-Match` não é usado para essas edições |

## Operações e idempotência

As APIs usam OpenAPI 3.1.0, `/api/v1`, UUIDs, datas com fuso, decimais em strings, JWT e erro comum. `Idempotency-Key` tem escopo por ator, método e caminho, com retenção mínima proposta de trinta dias. A chave HTTP é distinta de `messageId` e `operationId`.

`GET /planos-alocacao` permite localizar planos. `GET /capacidades/{id}` permite consultar uma capacidade criada. Nenhuma operação HTTP pública cria Compra diretamente ou substitui os comandos internos de reserva e agendamento.

## Alternativas consideradas

- Omitir escola, valores e vínculos deixaria os clientes sem dados necessários ao fluxo.
- Acrescentar consultas síncronas de Entregas a Editais mudaria as dependências de comunicação; o provisionamento interno deve ser definido explicitamente.
- Fixar prioridades ou percentuais legais no schema impediria tratar critérios como dados configuráveis do edital.

## Consequências

Os contratos apresentam schemas completos e regras de integração explícitas. As propostas de provisionamento institucional, critérios, valores e realocação precisam ser confirmadas antes da implementação. Validação estrutural não comprova autorização em execução nem disponibilidade dos recursos.

Alterações nessas decisões devem atualizar contratos, exemplos, modelos de dados e mensagens afetadas em conjunto.
