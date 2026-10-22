# ADR 0001 — Decomposição em quatro serviços de domínio

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** equipe CampoConecta
- **Relacionados:** [`01-servicos.md`](../parte2/01-servicos.md), [`ADR 0003`](./0003-cqrs-em-compras.md)

## Contexto

O enunciado exige pelo menos quatro serviços independentes, cada um com banco próprio. O domínio (PNAE) tem quatro ciclos de vida distintos: demanda pública (edital), capacidade de fornecimento, compromisso comercial e logística. Era preciso escolher um critério de corte que sustentasse uma SAGA de pelo menos três serviços e permitisse evolução independente.

## Decisão

Adotamos quatro serviços: **Editais**, **Ofertas**, **Compras** e **Entregas**, cortados por **ciclo de vida e regra de negócio própria**, não por tabela.

- `Prefeitura` e `Escola` pertencem a **Editais** (lado da demanda).
- `Produtor` pertence a **Ofertas** (identidade e produção evoluem juntas).
- `Proposta`, `PlanoAlocacao`, `Compra`, a SAGA e a liberação de pagamento pertencem a **Compras**.
- `CapacidadeLogistica`, `Agendamento`, `Entrega` e o recebimento pertencem a **Entregas**.

## Alternativas consideradas

| Alternativa | Motivo da rejeição |
|---|---|
| Serviço único de cadastros | Baixa autonomia de negócio; todos dependeriam dele |
| Um serviço por tabela | Comunicação excessiva sem fronteira útil |
| Serviço de Instituições separado de Editais | Chamada remota na publicação do edital sem ganho |
| Serviço de Pessoas separado de Ofertas | O produtor não tem regra própria além de ofertar |
| Fundir Editais e Compras | Duas razões para mudar; compensações internas |
| Orquestrador como serviço autônomo | Duplicaria o estado da compra em dois bancos |

## Consequências

**Positivas:** transações locais em cada serviço; compensações explícitas; SAGA atravessa quatro serviços; cada serviço pode evoluir sem coordenação.

**Negativas:** consultas de acompanhamento exigem composição (resolvido por CQRS em Compras); snapshots precisam ser mantidos; o serviço Compras concentra mais regra e precisa de módulos internos bem definidos.

## Referências

- `docs/parte2/00-base-comum.md`, seções 4 e 5
- `docs/parte2/01-servicos.md`, seções 2 a 4
