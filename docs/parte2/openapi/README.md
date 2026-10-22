# Contratos REST

Os quatro contratos de domínio descrevem APIs internas; os dois contratos de BFF descrevem o acesso externo pelo gateway. Não há implementação ou implantação. A [documentação de gateway, BFFs e HATEOAS](../04-gateway-bffs.md) complementa os schemas; o [relatório de validação](VALIDACAO.md) registra verificações e limites.

| Contrato OpenAPI 3.1.0 | Superfície |
|---|---|
| [Editais](editais.openapi.json) | Prefeitura, escolas, rascunho, consulta, edição, publicação e encerramento de edital |
| [Ofertas](ofertas.openapi.json) | Produtor, ofertas, saldo livre, inativação e consulta de reserva |
| [Compras](compras.openapi.json) | Propostas, retiradas, sugestão/ajuste/homologação de planos, compras, acompanhamento e liberação de pagamento |
| [Entregas](entregas.openapi.json) | Capacidade logística, consulta de entrega e confirmação de recebimento |
| [BFF prefeitura](bff-prefeitura.openapi.json) | Portal de gestor/escola, dashboard, página e ordenação, respostas aninhadas e ações autorizadas |
| [BFF produtor](bff-produtor.openapi.json) | Aplicativo, inicio, cursor, sincronização observada, ETag e compra achatada |

Cada arquivo é autocontido, com parâmetros, schemas, exemplos de corpos, respostas de erro e autenticação. JSON é um formato aceito por OpenAPI; não depende de resolver schemas em outro repositório. Pode ser aberto em um visualizador OpenAPI local.

## 1. Escopo e decisões

As APIs de domínio mantêm a autoridade sobre dados e operações; os BFFs adaptam as respostas para cada cliente. O [ADR 0006](../../adr/0006-conciliacao-contratos-rest.md) registra regras de integração propostas. O [ADR 0007](../../adr/0007-acesso-gateway-bffs.md) descreve o acesso pelo gateway e pelos BFFs.

## 2. Convenções de dados

| Tema | Contrato |
|---|---|
| Caminhos | Prefixo `/api/v1` em `servers`; caminhos de recursos relativos ao prefixo |
| Identificadores | UUID; identidade provisionada com `sub`, `instituicaoId` ou `produtorId` vinculados aos registros de domínio |
| JSON | `camelCase`; campo omitido é diferente de `null`; schemas rejeitam campos desconhecidos e `null` não declarado |
| Instantes | ISO 8601 com fuso, como `2026-10-20T10:00:00-03:00`; uma data civil de entrega usa `YYYY-MM-DD` |
| Quantidade | `{ "valor": "100.00", "unidade": "kg" }`; decimal positivo, duas casas e até 12 dígitos inteiros; saldo pode ser zero |
| Valores monetários | `{ "valor": "5.00", "moeda": "BRL" }`; decimal não negativo em string, duas casas, até 12 dígitos inteiros; moeda com três letras; regra de formação do total está proposta no ADR 0006 |
| Auditoria | `X-Correlation-Id` UUID opcional na entrada, gerado se ausente e devolvido em todas as respostas; `correlationId` também no erro |
| Validação | Erros de schema, query, data, UUID, cabeçalho obrigatório ou campo desconhecido usam `400`; eventual FastAPI deve adaptar o `422` padrão para este contrato |

Prazos precisam ser futuros quando exigido pela operação; janelas exigem início anterior ao fim. Intervalos de consulta têm limites inclusivos e `inicioDesde <= inicioAte`. Quantidade e saldo precisam usar a mesma unidade do item/oferta; não há conversão implícita. Capacidade logística usa kg no modelo logístico: outras unidades exigem conversão definida pelos donos antes do agendamento, sem somar unidades incompatíveis.

Exemplos são ilustrativos, com UUIDs válidos, e não cadastros reais ou comprovação de integração. Datas e dados documentais não dispensam validações de negócio no sistema futuro.

## 3. Recursos, métodos e códigos HTTP — Semântica HTTP

| Método/código | Uso e justificativa no projeto |
|---|---|
| `GET` / `200` | Consulta sem mudar estado. Inclui recursos individuais, coleções, resultado por item do plano e projeção de acompanhamento |
| `POST` / `201` | Criação local concluída de prefeitura, escola, produtor, oferta, edital, proposta, plano, capacidade ou confirmação de recebimento. `Location` identifica o recurso ou a coleção subordinada da confirmação |
| `POST` / `200` | Publicação, encerramento e retirada são transições concluídas localmente. Retornam o recurso atualizado; não criam registro HTTP independente com outro identificador |
| `POST` / `202` | Homologação aceita e persistida: compras, SAGAs e outbox são criadas localmente, mas reservas/agendamento ainda são assíncronos. Corpo e `Location` apontam ao plano para consultar cada compra |
| `PATCH` / `200` | Ajuste parcial nos campos explicitamente aceitos pelo schema, com versão. O servidor retorna o recurso atualizado; omissões preservam valores |
| `400` | Formato, parâmetro, cabeçalho ou conteúdo inválido, incluindo dados não suportados pelo contrato |
| `401` | Token ausente/inválido/expirado; `WWW-Authenticate: Bearer` |
| `403` | Identidade autenticada sem papel ou vínculo para a operação |
| `404` | UUID de recurso inexistente; liberação ainda não registrada tem código específico `LIBERACAO_NAO_REGISTRADA` |
| `409` | Estado incompatível, saldo/regra de negócio em conflito, duplicidade, versão obsoleta, chave idempotente com outro conteúdo ou processamento da mesma chave ainda em curso |
| `503` | Dependência indispensável indisponível; `Retry-After` em segundos orienta nova tentativa. Não garante ausência de efeito se houve perda da resposta |

As transições são recursos subordinados (`publicacoes`, `encerramentos`, `retiradas`, `homologacoes`, `recebimentos`), preservando os nomes do projeto e delimitando regras de autorização. Sua semântica de negócio fica no serviço dono. O cliente não envia um novo `status` arbitrário por PATCH.

Não há `POST /compras`: a única criação de compras é a homologação de plano. Reservar/liberar demanda, reservar/liberar oferta e agendar/cancelar entrega não são ações HTTP do cliente. Cancelamento de compra já confirmada é outro processo, ainda fora desta superfície. A liberação de pagamento não é transferência bancária e não tem comando público de liberação.

`PUT` não foi incluído porque as edições são parciais; `DELETE` não foi incluído porque registros emitidos, reservas e compromissos precisam de rastreabilidade. Oferta/produtor são inativados com PATCH; proposta é retirada pela transição definida. Não há requisito de exclusão física nesta etapa.

PATCH usa `application/json` com schema específico por operação, não JSON Patch nem JSON Merge Patch. Arrays não têm comportamento genérico: ajustes de edital referenciam itens existentes sem incluir/remover; ajustes de plano informam por item uma nova quantidade **ou** `excluir: true`. IDs repetidos são inválidos. Edição em estado indevido retorna `409`; corpo sem mudança retorna `400`.

## 4. Versionamento

`openapi: 3.1.0` indica a linguagem do contrato; `info.version: 1.0.0` identifica esta edição documental; `/api/v1` é a versão pública da interface do serviço. São conceitos distintos.

Mudanças que preservam os consumidores permanecem em v1, como novas operações ou campos opcionais de resposta para clientes que ignorem campos desconhecidos. Remover/renomear campo, mudar seu tipo ou significado, exigir campo antes opcional e alterar paginação ou autorização de forma incompatível exigem avaliar uma nova versão de caminho. Novos valores de enum podem quebrar clientes com enum fechado; não são considerados automaticamente compatíveis.

Uma v2 exige contrato paralelo, relação dos consumidores afetados, orientação de migração e prazo acordado para retirada da v1. O contrato antigo permanece documentado durante a transição. Nenhuma data de desativação é inventada nesta entrega.

`versao` dentro do recurso é controle de concorrência, sem relação com v1 ou `info.version`. Ajustes/transições recebem a versão atual, e uma transação local só aplica a mudança se ela coincidir, incrementando o valor. Conflito usa `409`. Não se usa `If-Match` nessas edições, evitando atribuir `409` à semântica HTTP de precondição falha (`412`). ETag de sincronização móvel é assunto da BFFs.

## 5. Paginação e filtros

Todas as coleções dos quatro serviços de domínio usam `pagina` (padrão 1, mínimo 1) e `tamanho` (padrão 20, intervalo 1–50). Resposta: `items` e `paginacao {pagina, tamanho, total, totalPaginas}`. Página após a última retorna lista vazia com `200`; coleção vazia tem `total=0` e `totalPaginas=0`.

Ordenação fixa: `id` ascendente, estável dentro de uma consulta. Coleções são uma visão dos dados no momento de cada requisição: inserções entre páginas podem mudar o conjunto. Filtros são os enumerados em cada operação, escalares, combinados com AND, sem parâmetros repetidos. Query desconhecida/repetida ou valor inválido retorna `400`. Datas e UUIDs são percent-encoded quando necessário; não há filtro SQL livre nem ordenação arbitrária.

Autorização restringe o conjunto **antes** dos filtros, contagem e paginação. Um filtro não amplia o escopo: identificador de outra instituição/produtor deve ser rejeitado com `403` quando expressa acesso fora do vínculo; ausência de correspondência dentro do escopo retorna lista vazia. `total` conta apenas os recursos autorizados que atendem aos filtros.

O portal adapta a ordenação por campos enumerados e mantém página de até 50 itens. O BFF produtor usa cursor opaco de até dez registros, com `removidos`, `proximoCursor` opcional e `sincronizadoEm`. `atualizadoDesde` significa observação pelo BFF, não timestamp de escrita do domínio. O mecanismo está detalhado na [sincronização móvel](../04-gateway-bffs.md#32-sincronização-móvel-sem-alterar-as-apis-de-domínio); não acrescenta cursor ou novo banco aos serviços.

## 6. Autenticação e autorização por recurso

Os quatro contratos declaram Bearer JWT globalmente. A lista `x-papeis` e a regra `x-autorizacao` de cada operação documentam as permissões, pois um esquema HTTP Bearer não codifica papéis de domínio como scopes OAuth. BFF propaga a identidade autenticada; serviços não confiam em cabeçalhos de identidade arbitrários fornecidos pelo cliente.

- Gestor opera sobre a prefeitura de `instituicaoId` e suas escolas/recursos.
- Escola consulta seus recursos e confirma apenas entrega cujo `escolaId` coincida com `instituicaoId`. Gestor e produtor não confirmam recebimento.
- Produtor mantém seu cadastro/ofertas, envia e retira suas propostas e consulta suas compras/entregas, com `produtorId` do token.
- Produtor pode consultar editais publicados/encerrados, nunca rascunhos; escola recebe apenas itens vinculados a ela.

Vínculos são validados no modelo autoritativo ou no contexto interno autenticado que o alimenta, nunca em snapshots históricos de nomes nem em campos livres da requisição. A lacuna de provisionamento institucional em Entregas está explicitada no ADR 0006. Não há nova chamada HTTP entre serviços introduzida de forma implícita.

Consulta de acompanhamento autoriza pelo modelo de escrita antes de ler a projeção. Compra inexistente retorna `404`; compra existente ainda sem projeção retorna `503` com `Retry-After`. `updatedAt` informa quando o projetor aplicou o estado; a meta de 5 segundos não foi medida e não é SLA. A ausência de entrega antes do agendamento é representada por campo omitido.

## 7. Idempotência e repetição

Toda escrita (`POST`/`PATCH`) exige `Idempotency-Key` UUID. Escopo: identidade `sub` autenticada + método + caminho normalizado do serviço. Mesmo ator, chave, operação e corpo JSON semanticamente igual retornam o status, corpo e `Location` originais. A ordenação de chaves JSON não muda o conteúdo; a ordem de arrays faz parte do conteúdo.

Chave igual com conteúdo diferente retorna `409`, código `IDEMPOTENCY_KEY_REUTILIZADA`. Processamento simultâneo ainda sem resultado retorna `409`, código `OPERACAO_EM_ANDAMENTO`; cliente espera e repete com a mesma chave. Não dispara uma segunda operação.

A implementação futura deve persistir chave, impressão digital da requisição e resultado junto dos efeitos locais. Rejeições de negócio concluídas podem ser memorizadas; erros de formato/autenticação anteriores à execução não ocupam a chave. Falha técnica sem commit não conclui a chave e permite repetição. Se uma resposta se perder após commit, a repetição recupera o resultado persistido. Na validação de proposta, `503` de dependência ocorre antes de persistir proposta e não grava uma falsa resposta de sucesso.

Retenção mínima candidata: 30 dias, pendente de revisão no ADR 0006. Depois disso o resultado HTTP original não é garantido, mas unicidades de negócio — plano/item, reserva por operação, confirmação por entrega, liberação por compra — continuam protegendo os efeitos. Repetir homologação já concluída com nova chave resulta em `409`; a mesma chave devolve o `202` original. Consultar o plano revela o estado atual, que pode ter avançado desde aquela resposta.

Chave HTTP não substitui `messageId` (deduplicação de mensagem) ou `operationId` (identidade da operação da SAGA). O BFF deve preservar a chave em reenvios à mesma operação interna; divisão em múltiplas escritas exige definir chaves derivadas estáveis no contrato do BFF.

## 8. Erros

Todas as respostas de erro usam o schema `Erro` com `code`, `message`, `details` e `correlationId`. `details` é uma lista, vazia quando não houver indicação de campo. Mensagens não expõem stack trace, SQL ou segredos.

```json
{
  "code": "VERSAO_DESATUALIZADA",
  "message": "O recurso foi alterado. Consulte a versão atual antes de editar.",
  "details": [{"campo": "versao", "motivo": "A versão enviada não é a atual."}],
  "correlationId": "00000099-0000-4000-8000-000000000001"
}
```

Códigos de máquina previstos além dos exemplos genéricos: `VERSAO_DESATUALIZADA`, `ESTADO_INCOMPATIVEL`, `IDEMPOTENCY_KEY_REUTILIZADA`, `OPERACAO_EM_ANDAMENTO`, `VINCULO_INVALIDO`, `LIBERACAO_NAO_REGISTRADA` e `PROJECAO_INDISPONIVEL`. O cliente decide por status/código, não por texto da mensagem. `503` sem resposta final conhecida exige repetir com a mesma chave para recuperar o resultado, não presumir cancelamento.

## 9. Cobertura e validação

| Tema | Evidência |
|---|---|
| Serviços | Quatro arquivos com as operações de cadastro, consulta e ciclo de vida; nenhuma criação pública de compra/reserva/agendamento |
| Schemas e convenções | Schemas de entrada/saída, exemplos, parâmetros, paginação, erros, JWT, papéis/vínculos e Idempotency-Key por operação; regras relacionais no texto das operações |
| Semântica HTTP | Seções 3 e 4: recursos, verbos, códigos, PATCH e evolução de versão |
| Gateway | Documento `04-gateway-bffs.md` e configurações em `gateway/nginx/`: rotas, verificação delegada, limites, TLS, CORS e responsabilidades |
| BFFs | Dois contratos de BFF com schemas, agregações e respostas diferentes, página versus cursor, ETag e sincronização |
| HATEOAS | `_links` em Compras e BFFs, matriz de papel/estado/vínculo e exemplos de escola, gestor e produtor |
| Validação | Relatório `VALIDACAO.md`, verificação estática reproduzível e ADR 0007 de acesso/BFFs |

O [relatório de validação](VALIDACAO.md) consolida os seis contratos, a cobertura de operações REST, exemplos, origens, links e o teste de sintaxe NGINX. Isso verifica o projeto estático, não a implementação futura.

Para validar estrutura e referências com Node.js/npm:

```powershell
npm exec --yes --package=@redocly/cli@2.8.0 -- redocly lint docs/parte2/openapi/editais.openapi.json docs/parte2/openapi/ofertas.openapi.json docs/parte2/openapi/compras.openapi.json docs/parte2/openapi/entregas.openapi.json docs/parte2/openapi/bff-prefeitura.openapi.json docs/parte2/openapi/bff-produtor.openapi.json --extends minimal
node docs/parte2/openapi/verificar-contratos.cjs
```

O comando baixa a ferramenta no cache npm e não adiciona dependências ao aplicativo. Validação estrutural não comprova implementação, autorização em execução, comportamento transacional ou consistência de integração. Esses pontos precisam de revisão e, na fase de implementação, testes de integração.

## 10. Referências técnicas

- [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html): estrutura dos contratos, schemas, parâmetros, segurança e exemplos.
- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html): métodos, códigos, Location, autenticação e precondições.
- [RFC 5789 — PATCH](https://www.rfc-editor.org/rfc/rfc5789.html): alteração parcial de recursos.

As regras de negócio, permissões e escolhas concretas de paginação/idempotência são decisões propostas do CampoConecta, e não requisitos impostos por essas referências.
