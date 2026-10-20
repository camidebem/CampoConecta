# Princípios, padrões de projeto e padrões arquiteturais

> Documento de apoio à **arguição**. Ele não repete a arquitetura: mostra **onde** cada princípio e padrão resolve um problema real do CampoConecta e **o que foi descartado**.
> Na Parte 2 esses itens são **decisões de projeto**; a implementação é da Parte 4.

## 1. Como ler este documento

Só incluímos um padrão quando ele responde a três perguntas: qual problema existia, por que a solução escolhida resolve e qual o custo aceito. Os padrões que consideramos e recusamos aparecem na seção 6 — saber por que **não** usar também é domínio do projeto.

## 2. Princípios de código

### 2.1 SOLID

| Princípio | Onde aparece no CampoConecta |
|---|---|
| **S — Responsabilidade Única** | Um serviço = uma responsabilidade de negócio (Editais não reserva produção; Entregas não define disponibilidade). Dentro do serviço, um caso de uso por operação: `HomologarPlano`, `RegistrarRecebimento`. |
| **O — Aberto/Fechado** | Critérios de alocação são `Strategy`: incluir "menor preço" ou "proximidade" é criar uma nova implementação, sem alterar o algoritmo que percorre as propostas. |
| **L — Substituição de Liskov** | Repositórios em memória usados nos testes substituem os repositórios PostgreSQL sem mudar o caso de uso. |
| **I — Segregação de Interface** | Portas estreitas: `EditalConsultaPort`, `OfertaReservaPort`, `RelogioPort`. Nenhum serviço recebe um cliente genérico do sistema inteiro. |
| **D — Inversão de Dependência** | Domínio e aplicação dependem de interfaces; FastAPI, `asyncpg`, `pika` e clientes HTTP ficam na infraestrutura e são injetados na composição. |

### 2.2 DRY, KISS, YAGNI e nomes

| Princípio | Aplicação | Cuidado |
|---|---|---|
| **DRY** | Envelope de mensagem, outbox, inbox e tratamento de erro em **biblioteca interna versionada** — uma implementação, não quatro | DRY **não** significa compartilhar banco, tabela ou modelo entre serviços. Duplicar um pequeno DTO entre serviços é melhor que acoplar |
| **KISS** | PostgreSQL único como tecnologia; *polling* no relay em vez de CDC; SAGA orquestrada em vez de coreografia | Simplicidade não é atalho: idempotência e compensação continuam obrigatórias |
| **YAGNI** | Sem serviço financeiro, sem notificação push, sem *cache* e sem LLM na Parte 2 | Reservar pontos de extensão (eventos de Compras) sem implementá-los agora |
| **Nomes canônicos** | `AlocarDemanda`, `ReservarOferta`, `AgendarEntrega`, `EntregaRecebida`, `AcompanhamentoCompra` | Mudança de nome compartilhado exige PR na base comum |

## 3. Padrões de projeto (GoF)

### 3.1 Criacionais

| Padrão | Onde | Problema resolvido |
|---|---|---|
| **Factory Method** | Criação de mensagens: `Mensagem.criar(tipo, payload, correlationId)` preenche `messageId`, `schemaVersion` e `occurredAt` | Impede mensagem sem envelope válido; um único ponto de geração de identidade |
| **Factory Method** | Homologação do plano cria `Compra` + `SagaCompra` a partir de `plano_item` | A criação do agregado e do processo fica em um só lugar, sempre consistente |
| **Singleton** | Configuração e *pool* de conexão, uma vez por processo | Evita recriar conexão por requisição. **Escopo é o processo**, não o sistema: um Singleton global entre serviços seria acoplamento |

### 3.2 Estruturais

| Padrão | Onde | Problema resolvido |
|---|---|---|
| **Adapter** | Relay do broker, cliente HTTP entre serviços, `authn-verify` e provedor OIDC | Isola bibliotecas e protocolos do domínio; trocar RabbitMQ por outro broker não altera regra de negócio |
| **Facade** | BFF prefeitura e BFF produtor | Cliente recebe uma resposta pronta em vez de orquestrar quatro serviços |
| **Decorator** | Retry, timeout e *circuit breaker* envolvendo um cliente (LLM na Parte 4; broker nesta) | Acrescenta resiliência sem alterar a interface do cliente |

### 3.3 Comportamentais

| Padrão | Onde | Problema resolvido |
|---|---|---|
| **Strategy** | Critérios de alocação do edital (lista ordenada e parametrizável) | Novo critério sem `if/else` crescente; o critério é **dado** do edital, a estratégia é código |
| **Observer** | Transição de `Compra` → evento no outbox → projetor e BFFs | Desacopla quem muda o estado de quem precisa saber |
| **State** | `SagaCompra` (`EM_ANDAMENTO`, `COMPENSANDO`, `CONCLUIDA`, `CANCELADA`) e `Compra` | Transições válidas concentradas; estado inválido não é representável |
| **Command** | `AlocarDemanda`, `ReservarOferta`, `AgendarEntrega` e suas compensações | Intenção de negócio explícita, serializável, idempotente e auditável |
| **Template Method** | Consumidor base (inbox → handler → *ack*) e relay base | Evita repetir o mesmo esqueleto de consumo nos quatro serviços |

## 4. Padrões arquiteturais

| Padrão | Onde | Problema resolvido |
|---|---|---|
| **Database per Service** | Quatro instâncias PostgreSQL | Autonomia transacional e isolamento de falha |
| **SAGA (orquestrada)** | Compras | Transação de negócio distribuída com compensações explícitas |
| **CQRS** | Compras / `AcompanhamentoCompra` | Leitura que exigiria quatro serviços vira uma consulta |
| **Transactional Outbox** | Todos os serviços | Elimina dual write banco/broker |
| **Idempotent Consumer (Inbox)** | Todos os consumidores | Reentrega sem efeito duplicado |
| **API Gateway** | NGINX + `auth_request` | Entrada única, autenticação e rate limiting |
| **Backend for Frontend** | BFF prefeitura e BFF produtor | Cada cliente recebe o payload adequado ao seu dispositivo e uso |
| **Event-driven** | Comandos e eventos da SAGA | Acoplamento temporal fraco entre serviços |
| **Layers + Ports & Adapters** | Estrutura interna de cada serviço | Domínio testável sem infraestrutura |
| **Modularização por domínio** | `compras/propostas`, `compras/alocacao`, `compras/saga`… | Organização por funcionalidade, não por tipo técnico (`models/`, `controllers/`) |

## 5. Mapa: padrão → documento

| Assunto | Documento |
|---|---|
| Fronteiras, SRP por serviço, camadas internas, Strategy/State/Command | [`01-servicos.md`](./01-servicos.md) |
| Repository, Unit of Work, concorrência, Outbox, Inbox, DLQ | [`02-dados-outbox.md`](./02-dados-outbox.md) |
| CQRS, Observer (evento → projeção), reconstrução | [`03-cqrs.md`](./03-cqrs.md) |
| Decisões registradas | [`docs/adr/`](../adr/) |
| SAGA, compensações e catálogo de mensagens | frente Pessoa 3 (`05-saga.md`, `06-mensagens.md`) |
| Gateway, BFFs e HATEOAS | frente Pessoa 2 (`04-gateway-bffs.md`) |

## 6. Anti-padrões evitados

| Anti-padrão | Por que não entra |
|---|---|
| **Shared database** | Recria acoplamento por dados e impede evolução independente |
| **Dual write** (banco + broker separados) | Perda silenciosa de evento; substituído por outbox |
| **Transação distribuída (2PC)** | Frágil, cara e incompatível com autonomia dos serviços |
| **Monólito distribuído** | Serviços que só funcionam juntos não são microsserviços; aqui cada um responde sozinho ao seu dono |
| **Comunicação "tagarela"** | Várias chamadas para uma tela; resolvido por BFF e projeção |
| **Modelo anêmico** | Invariantes (saldo, estados, unicidade) ficam no domínio e no banco, não no controller |
| **Smart UI** | BFF adapta e agrega, mas não decide regra de negócio |
| **Golden hammer** | Não se usa fila para consulta nem HTTP para efeito de negócio |

## 7. O que ainda não é implementação

Nenhum destes padrões está codificado nesta etapa. O que existe é a decisão documentada, com contrato e justificativa — condição para a Parte 2. A verificação real (testes, métricas de *lag*, reconstrução da projeção) acontece na Parte 4, quando o sistema rodar.
