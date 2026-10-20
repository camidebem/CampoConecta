# Anexo A — Plano de trabalho da Parte 2

> Material de organização interna. Pode ser movido para `docs/planejamento/` se o grupo preferir manter `docs/parte2/` apenas com a arquitetura.

## A.1 Donos dos documentos

| Caminho | Dono |
|---|---|
| `README.md` | Pessoa 1, com contribuições das outras |
| `01-servicos.md`, `02-dados-outbox.md`, `03-cqrs.md` | Pessoa 1 |
| `openapi/` (serviços e BFFs), `04-gateway-bffs.md` | Pessoa 2 |
| `05-saga.md`, `06-mensagens.md` | Pessoa 3 |
| `07-validacao.md` | Pessoa 3, revisado por todos |
| `00-base-comum.md` | Compartilhado, alterado só por PR |
| `docs/adr/` | Cada pessoa na sua frente |

## A.2 Tarefas

### Pessoa 1 — Serviços, dados e CQRS

- [ ] **P1-01:** detalhar os quatro serviços, justificar fronteiras e alternativas descartadas (incluindo Escola/Prefeitura em Editais e Produtor em Ofertas).
- [ ] **P1-02:** diagramas de componentes e de comunicação, com gateway, `authn-verify`, BFFs, broker e quatro bancos.
- [ ] **P1-03:** entidades, referências externas, snapshots, instâncias e credenciais; justificar PostgreSQL por serviço.
- [ ] **P1-04:** concorrência nas reservas, consistência eventual (lista de pontos) e pontos de dual write.
- [ ] **P1-05:** outbox, relay e inbox, retries e falhas entre publicação e confirmação.
- [ ] **P1-06:** CQRS de Compras: schemas conceituais da projeção, eventos de atualização, atraso e reconstrução a partir do modelo de escrita.
- [ ] **P1-07:** README/índice e ADR de serviços, dados e CQRS.

**Aceite:** identifica-se o dono de cada dado, explica-se o que ocorre se o relay cair e mostra-se como uma escrita chega à consulta. Nenhum diagrama tem banco compartilhado.

### Pessoa 2 — REST, gateway e BFFs

- [ ] **P2-01:** OpenAPI dos quatro serviços, com a superfície da seção 6.2 e todo o ciclo de vida necessário (incluindo planos de alocação e homologação).
- [ ] **P2-02:** parâmetros, schemas, exemplos, erros, paginação, autorização e idempotência.
- [ ] **P2-03:** justificar versionamento e uso de recursos, verbos e códigos.
- [ ] **P2-04:** NGINX com `auth_request`: rotas externas e internas, responsabilidades de cada camada e alternativas avaliadas.
- [ ] **P2-05:** OpenAPI dos dois BFFs (`/dashboard`, `/inicio`, listagens e ações) e comparação das respostas para a mesma compra.
- [ ] **P2-06:** HATEOAS de Compra com a divisão de responsabilidades entre Compras e BFF, links condicionados a estado e papel.
- [ ] **P2-07:** validar sintaxe e referências dos OpenAPI e registrar ADR de acesso e BFFs.

**Aceite:** outro integrante entende uma requisição do cliente até o serviço e constrói um cliente a partir do contrato, sem inventar campos. Os dois BFFs têm diferenças concretas de payload, agregação e propósito.

### Pessoa 3 — SAGA, mensagens e coerência final

- [ ] **P3-01:** justificar orquestração frente à coreografia e definir o estado persistido (Compra e SAGA).
- [ ] **P3-02:** comandos e eventos da tabela de passos, incluindo respostas de compensação.
- [ ] **P3-03:** sequência de sucesso atravessando os quatro serviços, a partir da homologação (1 plano, N SAGAs).
- [ ] **P3-04:** sequência de falha no agendamento, com todas as compensações pertinentes.
- [ ] **P3-05:** duplicação, timeout, resposta tardia, reinício e compensação incompleta.
- [ ] **P3-06:** envelope, payloads, correlação e versão dos eventos; eventos de transição de Compra consumidos pela projeção.
- [ ] **P3-07:** recebimento e liberação de pagamento; ADR da SAGA.
- [ ] **P3-08:** matriz de requisitos e roteiro de apresentação a partir dos documentos entregues.

**Aceite:** cada efeito tem compensação ou justificativa; a compra só termina cancelada após concluídas as compensações. Os diagramas usam exatamente os nomes e campos do catálogo de mensagens.

Os pesos da rubrica não equivalem a horas de trabalho. Se uma frente exceder as demais, redistribuir um arquivo inteiro, mantendo um dono por arquivo.

**Regras durante o trabalho**

1. Uma branch por frente (`docs/estrutura-dados`, `docs/apis-bffs`, `docs/saga`), integradas na branch apresentada antes do congelamento.
2. Cada pessoa altera seus arquivos; a base comum muda só por PR revisado por quem for afetado.
3. Nome de serviço, ID, estado, evento ou endpoint compartilhado não muda unilateralmente.
4. Uma mudança de contrato indica motivo, consumidores afetados e documentos a atualizar.
5. Pessoa 1 é autoridade sobre entidades; Pessoa 2, sobre HTTP; Pessoa 3, sobre mensagens. Conflitos são decididos pelos envolvidos e registrados na base.
6. Revisão cruzada: Pessoa 1 revisa a SAGA; Pessoa 3, APIs e BFFs; Pessoa 2, serviços, dados e CQRS.
7. Todos produzem commits próprios, com `user.name` e `user.email` corretos, e usam `Co-authored-by` em trabalho em pares.

| Data | Resultado |
|---|---|
| 18/10 | Base conferida, responsáveis definidos e skeletons compartilhados |
| 19/10 | Primeiras versões das três frentes |
| 20/10 | Revisão cruzada e correção de inconsistências; conferir o sorteio |
| 21/10, até 18h | Integração final na branch apresentada e ensaio |
| 21/10, antes de 23h59 | Verificar repositório público, autoria, links e commit final |

## A.3 Matriz de fechamento

| Requisito | Responsável | Evidência | Verificação |
|---|---|---|---|
| Quatro serviços | Pessoa 1 | `01-servicos.md` | Responsabilidades distintas e fronteiras justificadas |
| REST completo | Pessoa 2 | `openapi/` | Schemas e referências válidos; exemplos coerentes |
| Versionamento e HATEOAS | Pessoa 2 | OpenAPI e exemplos | Links utilizáveis via gateway e ações autorizadas |
| Gateway | Pessoa 2 | `04-gateway-bffs.md` | Rotas e autenticação chegam aos destinos corretos |
| Dois BFFs/clientes | Pessoa 2 | Contratos e comparação | Diferenças explícitas de agregação, payload e respostas |
| Bancos, consistência e outbox | Pessoa 1 | `02-dados-outbox.md` | Instâncias separadas, dual write e duplicação tratados |
| SAGA | Pessoa 3 | `05-saga.md` e `06-mensagens.md` | Sucesso/falha, compensações e persistência definidos |
| CQRS | Pessoa 1 | `03-cqrs.md` | Escrita e leitura distintas, atualização, atraso e reconstrução definidos |
| Transversais | Todos | README e GitHub | Público, autoria, PRs, correções da etapa anterior |
| Apresentação | Todos | `07-validacao.md` | Cada integrante explica parte substantiva e responde sobre o todo |

**Revisão de ponta a ponta:** seguir uma compra pelos documentos, da requisição no gateway/BFF e da homologação até a SAGA, os bancos, o outbox e a projeção de leitura. Repetir com falha no agendamento e conferir recebimento e liberação de pagamento. Nomes, IDs, estados e mensagens precisam coincidir em todas as frentes.

**Revisão técnica final:** validar os OpenAPI com ferramenta adequada, renderizar todos os diagramas Mermaid, conferir links relativos, remover exemplos contraditórios, identificar metas ainda não medidas e não apresentar decisão proposta como resultado implementado.

**Composição do grupo:** o enunciado prevê quatro integrantes, com contribuição e apresentação de todos. Este plano distribui a produção entre três pessoas conforme decisão do grupo; a regra da disciplina não muda.

