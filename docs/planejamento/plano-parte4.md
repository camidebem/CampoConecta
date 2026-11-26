# Plano de trabalho da Parte 4 — Sistema em funcionamento

> Organização interna do grupo. A Parte 4 é apresentada **ao vivo**: fluxo de ponta a ponta, SAGA com falha e compensação provocada na hora, CQRS refletindo uma escrita, bancos separados evidenciados e uma funcionalidade com LLM (RAG + LangChain + resiliência).

## 1. Datas

| Quando | O quê |
|---|---|
| Até **28/11** | Contratos da seção 4 combinados entre os três; cada um cria a sua branch |
| **28/11 a 04/12** | Desenvolvimento em paralelo (o front usa dados de exemplo até a SAGA e o assistente ficarem prontos) |
| **05/12 a 07/12** | Integração: SAGA pelo front, falha e compensação, CQRS atualizando, assistente no app do produtor |
| **08/12** | Ensaio completo da demonstração; README de execução atualizado; PRs revisados |
| **09/12, 23h59** | **Congelamento do repositório** — tudo na `main` |
| 10/12 ou 15/12 | Apresentação (ordem sorteada em 08/12) |

## 2. Decisões tomadas

| Tema | Decisão |
|---|---|
| Front | **React + Vite**, uma aplicação com duas áreas (`/prefeitura` e `/produtor`) e um painel `/demo`, servida por um contêiner NGINX atrás do gateway |
| LLM | **Modelo local com Ollama**, em contêiner no compose |
| Roteiro da demonstração | A definir até 05/12 |

### 2.1 Proposta técnica para o LLM (confirmar no primeiro teste)

| Item | Proposta | Observação |
|---|---|---|
| Serviço | `assistente` (Python + FastAPI + LangChain), mesmo modelo base dos outros serviços | 5º serviço, com banco próprio |
| Modelo de geração | `qwen2.5:3b` ou `llama3.2:3b` no Ollama | Modelos pequenos (~2 GB), rodam em CPU; testar qualidade em português |
| Embeddings | `bge-m3` (multilíngue) ou `nomic-embed-text` no Ollama | Testar recuperação em português |
| Base vetorial | **pgvector** em `pg-assistente` | Mantém database per service e o padrão PostgreSQL |
| Base de conhecimento | Documentos públicos do PNAE: Lei 11.947/2009, resolução do FNDE e Caderno de Compras da Agricultura Familiar | Já usados como referência na Parte 1 |
| Propósito | Ajudar o produtor a participar das chamadas públicas: dúvidas sobre o processo (RAG) e editais abertos compatíveis com a produção dele (tool) | Acessado pelo app do produtor, via BFF produtor |
| Custo | Local: sem custo por token; a análise compara tempo de resposta e consumo de máquina com o custo estimado de uma API paga em escala | Exigido no enunciado |

**Risco principal:** desempenho do Ollama em CPU no Docker Desktop. Testar na primeira semana, em cada máquina, quanto tempo uma resposta leva. Se for lento demais, usar o modelo menor ou rodar o Ollama direto no Windows (fora do contêiner).

## 3. Divisão das frentes

| Pessoa | Frente | Branch sugerida |
|---|---|---|
| **José** | SAGA, outbox/relay/inbox e mensageria | `feat/saga` |
| **Camily** | CQRS e serviço `assistente` (LLM) | `feat/cqrs` e `feat/assistente` |
| **Daniel** | Front, BFFs e gateway | `feat/frontend` |

### José — SAGA e mensageria

- [ ] **J-01:** outbox + relay nos serviços (tabela `outbox`, publicação com *publisher confirm*, backoff). → [`02-dados-outbox.md`](../parte2/02-dados-outbox.md) §7
- [ ] **J-02:** inbox + consumidor com idempotência por `messageId`, retry e DLQ. → [`02-dados-outbox.md`](../parte2/02-dados-outbox.md) §8–§9
- [ ] **J-03:** Compras: plano de alocação e homologação (`POST /planos-alocacao`, `POST /planos-alocacao/{id}/homologacoes` → `202`). → contrato [`compras.openapi.json`](../parte2/openapi/compras.openapi.json)
- [ ] **J-04:** orquestrador: `saga_compra`, `saga_operacao`, avanço passo a passo e compensações em ordem inversa. → [`05-saga.md`](../parte2/05-saga.md) §4–§6
- [ ] **J-05:** participantes: `AlocarDemanda`/`LiberarDemanda` (Editais), `ReservarOferta`/`LiberarOferta` (Ofertas), `AgendarEntrega`/`CancelarAgendamento` (Entregas), com `UPDATE` condicional. → [`06-mensagens.md`](../parte2/06-mensagens.md) §3
- [ ] **J-06:** eventos para a projeção: `CompraCriada`, `SagaProgrediu`, `CompraConfirmada`, `CompraCancelada`. → [`03-cqrs.md`](../parte2/03-cqrs.md) §4
- [ ] **J-07:** cenário de falha reproduzível: escola sem capacidade logística na janela → `AgendamentoRejeitado` → `LiberarOferta` → `LiberarDemanda` → Compra `CANCELADA`. → [`05-saga.md`](../parte2/05-saga.md) §8

**Aceite:** pelo front, uma homologação confirma a compra (caminho feliz) e outra, para a escola sem capacidade, termina `CANCELADA` com saldo e produção devolvidos; dá para mostrar no banco de cada serviço o efeito e a compensação.

### Camily — CQRS e assistente com LLM

- [ ] **C-01:** Editais: `POST /editais/{id}/publicacoes` (hoje a publicação só existe como fixture SQL nos testes). → contrato [`editais.openapi.json`](../parte2/openapi/editais.openapi.json)
- [ ] **C-02:** CQRS: projetor que consome os eventos de Compras e grava `acompanhamento_compra`; `GET /compras/{id}/acompanhamento` lendo só a projeção. → [`03-cqrs.md`](../parte2/03-cqrs.md)
- [ ] **C-03:** infraestrutura do LLM no compose: `ollama` (com volume para os modelos), `pg-assistente` com pgvector, serviço `assistente`.
- [ ] **C-04:** RAG: ingestão dos documentos, divisão em trechos, embeddings, gravação no pgvector, recuperação e geração com chain do LangChain.
- [ ] **C-05:** tool do LangChain que consulta os editais abertos em Editais (dados reais do sistema).
- [ ] **C-06:** resiliência (pelo menos 2 exigidas): timeout + retry com backoff, cache das respostas, fallback quando o modelo cai (devolver os trechos recuperados) e, se der tempo, circuit breaker.
- [ ] **C-07:** avaliação do RAG: 5 ou mais perguntas de teste, comparando a resposta com e sem recuperação.
- [ ] **C-08:** análise de latência (tempo medido) e de custo por operação em escala; ADR da escolha do modelo local.

**Aceite:** uma escrita em Compras aparece no acompanhamento em poucos segundos; o assistente responde uma dúvida do PNAE citando o documento e lista editais reais; com o Ollama parado, o assistente responde pelo fallback em vez de travar.

### Daniel — Front, BFFs e gateway

- [ ] **D-01:** projeto React + Vite, Dockerfile multi-stage (Node faz o build, NGINX serve), contêiner `frontend` no compose e rota `/` no gateway (mesma origem, sem CORS).
- [ ] **D-02:** área `/prefeitura` (portal, tela larga): editais, propostas, plano de alocação, homologação e acompanhamento das compras.
- [ ] **D-03:** área `/produtor` (layout de celular): editais, ofertas, envio de proposta e tela do assistente.
- [ ] **D-04:** painel `/demo` para a apresentação: linha do tempo da SAGA por compra, compras confirmadas e canceladas, acompanhamento (CQRS) atualizando e indicadores do assistente.
- [ ] **D-05:** endpoints novos nos BFFs que o front precisar, sempre passando pelo gateway. → [`04-gateway-bffs.md`](../parte2/04-gateway-bffs.md)
- [ ] **D-06:** rota do assistente pelo BFF produtor (`/produtor/api/v1/assistente/...`).
- [ ] **D-07:** script de dados de demonstração (prefeitura, escolas, editais, produtores, ofertas, e uma escola sem capacidade para a falha).
- [ ] **D-08:** README: como subir tudo do zero, incluindo o download dos modelos do Ollama.

**Aceite:** a demonstração inteira é feita pelo navegador em `http://localhost:8080`, sem precisar do terminal, exceto para evidenciar os bancos separados.

## 4. Contratos a combinar até 28/11

| Contrato | Entre | O que fixar |
|---|---|---|
| Endpoints que o front usa | Daniel ↔ José, Camily | Caminhos nos BFFs, campos e exemplos de resposta (para o front usar mock no começo) |
| Estado da SAGA para o painel | José ↔ Daniel | Como o painel lê as etapas de cada compra (campos do acompanhamento ou endpoint próprio) |
| Eventos da projeção | José ↔ Camily | Nomes, payload e `aggregateVersion` dos 4 eventos de Compras (já definidos em [`06-mensagens.md`](../parte2/06-mensagens.md)) |
| API do assistente | Camily ↔ Daniel | Ex.: `POST /api/v1/perguntas` com `{ pergunta, produtorId }` → `{ resposta, fontes, usouFallback, latenciaMs }` |
| Dados de demonstração | Todos | Quais cadastros existem e qual escola provoca a falha |

## 5. Regras

1. Uma branch por frente, PR revisado por outra pessoa e commits pequenos ao longo das duas semanas (a distribuição no tempo conta na nota individual).
2. Ninguém fica bloqueado: enquanto a dependência não fica pronta, usar dados de exemplo e trocar depois, como na Parte 3.
3. `docker compose up -d --build` precisa continuar subindo tudo a partir da `main` depois de cada merge.
4. Senhas e configurações só no `.env`; o `.env.example` é atualizado junto com cada variável nova.
5. Na apresentação, os três falam sobre a própria frente e precisam conseguir responder sobre as dos outros (a arguição é nominal).
