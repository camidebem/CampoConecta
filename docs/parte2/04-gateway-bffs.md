# Gateway, BFFs e HATEOAS

Este documento descreve o gateway, a apresentação por cliente e os links de navegação e ação. As decisões de acesso estão no [ADR 0007](../adr/0007-acesso-gateway-bffs.md); regras de integração propostas estão no [ADR 0006](../adr/0006-conciliacao-contratos-rest.md).

Tudo aqui é projeto documental: não há BFF, verificador JWT ou serviços implementados, nem gateway implantado. Os arquivos NGINX são referência de configuração. Cada serviço mantém seus próprios dados, regras e transações.

## 1. Entrada única e rotas

| Entrada no gateway | Destino e caminho resultante | Identidade aceita |
|---|---|---|
| `/prefeitura/api/v1/*` | `bff-prefeitura:8000/api/v1/*` | `gestor` ou `escola`, sujeito às permissões de cada operação |
| `/produtor/api/v1/*` | `bff-produtor:8000/api/v1/*` | `produtor` |
| `/health` | Resposta local `200 {"status":"ok"}` | Pública; indica o gateway, não disponibilidade de todos os serviços |
| `/_auth` | Subrequest interno para `authn-verify:8000/verify` | Não é rota pública |
| Demais caminhos | `404` | Sem acesso direto aos serviços |

O prefixo do cliente é removido uma vez. Por exemplo, `/prefeitura/api/v1/compras/ID` chega ao BFF como `/api/v1/compras/ID`, que consulta `http://compras:8000/api/v1/compras/ID`. A query é preservada. Endereços são propostos para a rede interna, não URLs implantadas.

| BFF | Serviços permitidos | Banco de domínio |
|---|---|---|
| Prefeitura | Editais, Compras e Entregas | Nenhum |
| Produtor | Editais, Ofertas, Compras e Entregas | Nenhum |

Cada operação dos contratos externos declara `x-origens` com método e caminho das consultas internas. Uma operação de escrita corresponde a uma única escrita no serviço dono, com a identidade e a chave idempotente preservadas. Agregações fazem apenas consultas. Não há endpoint externo para reservar/liberar saldo, cancelar agendamento ou criar Compra diretamente.

## 2. Responsabilidades e autenticação

| Componente | Responsabilidade |
|---|---|
| Gateway NGINX | TLS, roteamento, CORS, corpo máximo, limites por IP/identidade, remoção/substituição de headers de identidade, correlação e logs |
| `authn-verify` | Validar JWT com JWKS do emissor configurado; verificar compatibilidade entre papel e prefixo; devolver claims confiáveis para o gateway, sem banco próprio |
| BFF | Restringir operações ao cliente/papel, adaptar payload, agregar APIs, transformar paginação, reescrever links/Location e manter cache técnico de apresentação |
| Serviço de domínio | Revalidar identidade confiável e vínculo com o recurso, aplicar regras de negócio, transação local, idempotência e eventos |
| Provedor OIDC | Usuários, credenciais, emissão de tokens e provisionamento de vínculos; não é serviço de domínio |

O gateway não julga proposta, homologa plano, reserva saldo nem confirma recebimento. O BFF não acessa SQL, não altera a projeção e não decide pagamento. Autenticar na borda não dispensa autorização por recurso no serviço.

### 2.1 Contrato do verificador interno

Subrequest `GET /verify`, sem corpo. Recebe `Authorization`, `X-Original-URI`, `X-Original-Method` e `X-Correlation-Id`. O caminho original é usado apenas para verificar o prefixo; não é interpretado como autorização sobre o UUID do recurso.

| Resultado | Resposta do verificador |
|---|---|
| Token válido, claims necessárias e papel compatível com prefixo | `204`, sem corpo; headers `X-Authenticated-Subject`, `X-Authenticated-Role`, e `X-Authenticated-Institution` ou `X-Authenticated-Producer` |
| Token ausente, inválido ou expirado | `401`, `WWW-Authenticate: Bearer` |
| Token válido com papel/prefixo incompatível | `403` |
| Não foi possível obter chave confiável para validar | Falha técnica; gateway responde `503`, nunca autoriza por ausência de validação |

O verificador exige assinatura válida, algoritmo permitido na configuração, emissor e audiência esperados, expiração e `nbf` quando presente. Não aceita `alg=none`, não escolhe emissor/JWKS por URL livre no token e não trata mera decodificação do JWT como autenticação. Cache de JWKS fica em memória com expiração e atualização controladas; se não existir chave confiável, falha fechada. Claims de papel e vínculo são verificadas antes de responder `204`; esse resultado nunca pode vir sem `sub` válido.

O gateway só aceita os headers de identidade produzidos por esse subrequest e os substitui no caminho de entrada. Headers alternativos como `X-User-Id` não são reconhecidos como identidade. BFFs e serviços continuam recebendo o Bearer JWT e devem usar somente a identidade validada, não nomes ou IDs livres do corpo. Não há token, senha ou payload de proposta nos logs de acesso.

A regra `gestor`/`escola` → prefeitura e `produtor` → produtor é executada pelo verificador delegado, como parte da responsabilidade de borda do gateway. As regras específicas — por exemplo, apenas escola vinculada pode receber — permanecem no serviço.

### 2.2 Configuração NGINX de referência

- [nginx.conf](gateway/nginx/nginx.conf): TLS, mapas, zonas, upstreams e os dois listeners.
- [externo.conf](gateway/nginx/externo.conf): limite IP, `auth_request` e headers confiáveis.
- [interno.conf](gateway/nginx/interno.conf): encaminhamento do listener privado aos BFFs.
- [erros.conf](gateway/nginx/erros.conf): erros JSON gerados pela borda.

O pacote escolhido precisa incluir `ngx_http_auth_request_module`. O exemplo usa NGINX de código aberto com verificação JWT delegada, sem depender do módulo comercial de JWT.

O primeiro listener termina TLS e autentica. Depois encaminha para `127.0.0.1:8081`, no mesmo gateway, que aplica `limit_req` pela identidade confiável e roteia ao BFF. Esse segundo listener fica restrito ao loopback; não deve ser publicado em Service, balanceador ou porta externa.

Os dois saltos evitam usar claims ainda vazias em `limit_req`: o limite por IP é aplicado antes da autenticação; o limite por identidade é aplicado em uma nova requisição interna, quando `X-Authenticated-Subject` já foi definido pelo subrequest anterior. Um `if` na fase de rewrite também não é usado para decidir papel a partir de variável que só será preenchida depois por `auth_request`.

Parâmetros propostos: 10 req/s por IP, burst 20; 5 req/s por identidade, burst 10; corpo até 1 MiB; conexão ao upstream até 2 s; leitura/escrita até 10 s. São configurações iniciais, não valores medidos. `429` expõe `Retry-After`; corpo excessivo usa `413`. Falha técnica de autenticação, conexão ou timeout usa `503`. Respostas de negócio dos BFFs não são convertidas em erros genéricos pelo proxy.

`X-Correlation-Id` UUID válido é preservado; se ausente/inválido, é gerado a partir do identificador aleatório do NGINX. A borda publica o mesmo valor na resposta e o encaminha nos dois saltos. `Location`, `ETag`, `If-None-Match` e `Idempotency-Key` atravessam o proxy; o BFF reescreve `Location` e links, sem expor host interno. Não há retry automático de escrita no gateway.

O exemplo permite CORS apenas para `https://portal.campoconecta.example`, com Bearer explícito, sem cookies de sessão. Aplicativo nativo não depende de CORS. Preflight de prefixos conhecidos retorna `204` sem autenticação e sem chamar domínio; a requisição efetiva continua exigindo token. A origem ilustrativa deve ser substituída na implantação. CORS não autoriza usuário.

Certificados em `certs/tls.crt` e `certs/tls.key`, DNS dos upstreams, diretórios `logs/` e `temp/` e módulos precisam existir no ambiente futuro. Nenhum certificado/chave privada foi incluído no repositório. Antes de iniciar, validar com `nginx -t -p <prefixo-absoluto>/ -c nginx.conf`. A [evidência de validação](openapi/VALIDACAO.md) distingue sintaxe testada de integração ainda inexistente.

## 3. Por que dois BFFs

| Aspecto | Prefeitura/escola — portal | Produtor — aplicativo |
|---|---|---|
| Objetivo | Supervisão, revisão e decisão em tela ampla | Consulta rápida e ações curtas em rede móvel |
| Agregação | `GET /dashboard`: editais, saldo, compras por estado e entregas atrasadas | `GET /inicio`: propostas recentes, próximas entregas e editais compatíveis com suas ofertas |
| Payload de compra | Objetos de edital/produtor/escola, estado da SAGA, entrega e pagamento | Produto, quantidade, destino, data e estado do pagamento, achatados |
| Coleções | Página de até 50 itens, filtros e ordenação por campos enumerados | Cursor opaco, até 10 registros por resposta, campos compactos |
| Escritas | Cadastros institucionais, edital, ajuste/homologação de plano, capacidade e recebimento pela escola | Cadastro próprio, ofertas, envio e retirada de proposta |
| Sincronização | Consulta direta ao serviço, sem cache de regra de negócio | ETag, revalidação e mudanças observadas desde `atualizadoDesde` |

Contratos: [BFF prefeitura](openapi/bff-prefeitura.openapi.json) e [BFF produtor](openapi/bff-produtor.openapi.json). Não são dois proxies com nomes diferentes: têm operações, schemas de consulta, agregações e mecanismos de paginação distintos. Operações de escola são um subconjunto das rotas do portal, não permissões de gestor.

### 3.1 Composição e falhas

`/dashboard` percorre as páginas autorizadas de Editais, Compras e Entregas. Conta editais `PUBLICADO`, agrupa compras por estado autoritativo e considera atrasada a entrega `AGENDADA` cuja `janela.fim` seja anterior a `consultadoEm`. Para escola, restringe itens e entregas à sua escola antes de contar. Um saldo exibido não garante uma reserva futura.

`/inicio` consulta os quatro serviços, limita a três as propostas recentes e a três as próximas entregas; a contagem de editais considera pelo menos um item com produto e unidade iguais a uma oferta ativa. Trata-se de compatibilidade técnica, não de decisão de elegibilidade jurídica. Local da entrega vem do snapshot autorizado de Compra, sem consultar o banco de Editais. As regras de proposta continuam sendo verificadas no envio pelo serviço Compras.

As composições não formam uma transação ou snapshot global. Para não apresentar contagem parcial como total, falha de fonte necessária resulta em `503`. Limite operacional proposto: 10.000 registros percorridos por composição; ao exceder, `503` pede restringir a consulta. Esse limite evita leitura ilimitada, mas o custo e a meta de desempenho ainda precisam ser medidos.

A ordenação do portal é adaptada no BFF, pois os serviços têm ordenação fixa por ID. Os campos aceitos são enumerados por coleção nos contratos; desempate por UUID ascendente. O BFF consulta páginas autorizadas, ordena a visão em memória e depois aplica `pagina/tamanho`. Não envia cláusula SQL, ordenação arbitrária ou novo parâmetro não suportado ao serviço.

### 3.2 Sincronização móvel sem alterar as APIs de domínio

Os serviços atuais não oferecem cursor ou log incremental comum. O BFF produtor mantém um **cache técnico volátil por ator e consulta**, obtido por leitura das APIs autorizadas. Esse cache não é fonte de verdade e não recebe transações, saldos ou eventos de negócio diretamente.

1. Primeira consulta sem cursor/instante: materializa os registros autorizados e publica uma visão ordenada por ID, dividida em lotes de até dez.
2. Cursor assinado vincula `sub`, papel/vínculo, recurso, filtros, geração da visão, posição e expiração. Cursor de outro ator retorna `403`; adulterado retorna `400`; expirado ou sem cache correspondente retorna `410`.
3. Um cursor continua a mesma visão congelada por até dez minutos. Mudanças posteriores ficam para a próxima sincronização. Items e IDs em `removidos` somam no máximo dez por página.
4. Cada nova varredura compara o conteúdo canônico com a visão anterior. Alterações observadas e desaparecimentos do resultado geram entradas no histórico técnico, retido por trinta minutos. `removidos` também cobre registros que deixaram de atender ao filtro, não somente exclusão física.
5. `atualizadoDesde` é um limite **exclusivo de observação pelo BFF**. A resposta fixa um limite superior `sincronizadoEm`; todas as páginas da geração usam o mesmo limite. Depois da última página, o aplicativo guarda esse marcador para a próxima consulta.
6. Atribuição de marcadores é monotônica e serializada por ator/consulta, evitando perder mudanças com o mesmo instante. Marca futura retorna `400`; histórica anterior à retenção, reinício ou perda de cache retorna `410 SINCRONIZACAO_EXPIRADA`, seguido de sincronização completa pelo cliente.

O BFF suporta consulta de estado observado, não auditoria de cada mutação intermediária do domínio. Paginação dos serviços também não oferece snapshot global; alterações concorrentes durante uma varredura podem ser vistas na próxima. O aplicativo deve realizar sincronizações completas periódicas e sempre validar ações no dono do recurso. Nenhuma leitura incremental garante disponibilidade de oferta.

Escrita bem-sucedida invalida as visões técnicas afetadas para nova varredura; não é o cache que confirma a escrita. O desenho inicial pressupõe uma instância lógica do BFF com acesso ao seu cache; múltiplas réplicas exigem afinidade da sessão ou cache técnico compartilhado com isolamento por identidade. Isso será decidido na implantação, sem introduzir banco de domínio no BFF.

### 3.3 ETag e revalidação

Todos os GETs do aplicativo aceitam `If-None-Match`. Autenticação, autorização e atualização/revalidação da visão precedem a comparação. O ETag fraco identifica conteúdo canônico, escopo autenticado, filtros, geração e links. A comparação segue HTTP, incluindo lista de tags e `*`. Sem mudança, retorna `304`, com ETag e sem corpo.

O ETag pertence à representação externa do BFF, não à resposta bruta do serviço. O BFF não repassa a condição como se os contratos internos já suportassem a mesma representação; consulta as fontes necessárias e calcula sua própria revalidação.

Respostas incluem `Cache-Control: private, no-cache` e `Vary: Authorization`; CORS acrescenta a variação por origem na borda. Relógio de consulta não muda o hash sozinho: `sincronizadoEm` permanece estável enquanto o conteúdo não muda, salvo início de nova geração explícita. Não há cache público de dados do produtor nem `304` que dispense conferir vínculo. Mudança de claims/vínculo invalida a visão anterior.

## 4. Comparação da mesma compra

Exemplos para uma compra `CONFIRMADA`. IDs e contexto são os mesmos; o formato atende a cada cliente. Os exemplos completos, inclusive `_links`, estão nos dois OpenAPI.

Portal, consultado por gestor:

```json
{
  "cliente": "prefeitura",
  "compraId": "00000010-0000-4000-8000-000000000001",
  "status": "CONFIRMADA",
  "edital": {"id": "00000003-0000-4000-8000-000000000001", "titulo": "Chamada pública de alimentos"},
  "produtor": {"id": "00000005-0000-4000-8000-000000000001", "nome": "Produtor Exemplo"},
  "escola": {"id": "00000002-0000-4000-8000-000000000001", "nome": "Escola Exemplo"},
  "quantidade": {"valor": "100.00", "unidade": "kg"},
  "estadoSaga": "CONCLUIDA",
  "entrega": {"id": "00000015-0000-4000-8000-000000000001", "status": "AGENDADA", "data": "2026-11-25"},
  "pagamento": {"status": "AGUARDANDO_RECEBIMENTO"}
}
```

Aplicativo, consultado pelo produtor da compra:

```json
{
  "cliente": "produtor",
  "compraId": "00000010-0000-4000-8000-000000000001",
  "status": "CONFIRMADA",
  "produto": "Arroz",
  "quantidade": {"valor": "100.00", "unidade": "kg"},
  "localEntrega": "Escola Exemplo",
  "dataEntrega": "2026-11-25",
  "pagamento": "AGUARDANDO_RECEBIMENTO"
}
```

Esses trechos mostram os campos de negócio; a representação completa também exige `_links`. Histórico de transições não é inventado pelo BFF: os serviços atuais não o expõem por HTTP. A versão do portal preserva mais contexto e estado atual; uma futura linha do tempo precisa de contrato próprio do dono.

## 5. HATEOAS no recurso Compra

O contrato [Compras 1.1.0](openapi/compras.openapi.json) acrescenta `_links` à resposta de Compra, conforme responsabilidade já prevista no projeto. O serviço só monta links de seus recursos; BFFs reescrevem o prefixo e acrescentam relações com outros serviços.

| Relação | Quem produz | Condição |
|---|---|---|
| `self` | Compras; BFF reescreve | Todo ator autorizado a consultar a compra |
| `acompanhamento` | Compras; BFF reescreve | Todo ator autorizado; a projeção pode ainda estar indisponível |
| `liberacao-pagamento` | Compras; BFF reescreve | Compra `RECEBIDA`, liberação existente e papel `gestor` ou `produtor`; escola não recebe |
| `edital` | BFF | Referência de edital autorizada para o ator |
| `entrega` | BFF | Entrega identificada e leitura autorizada; ausente antes do agendamento |
| `confirmar-recebimento` | Somente BFF prefeitura | Papel `escola`, `instituicaoId == escolaId` autoritativo e entrega atualmente `AGENDADA`; para Compra confirmada |

Links usam `href` relativo à origem do gateway e `method` explícito. Na API interna começam em `/api/v1`; externamente começam em `/prefeitura/api/v1` ou `/produtor/api/v1`. O BFF aceita apenas relações e caminhos internos previstos, impedindo que um link de origem desconhecida seja transformado em destino arbitrário.

Para decidir uma ação, o BFF consulta a Compra autoritativa e, quando aplicável, Entregas. Não usa snapshot do nome da escola ou projeção possivelmente atrasada para conceder permissão. A confirmação volta a ser validada por Entregas no POST, porque o estado pode mudar entre leitura e ação. Falha da consulta decisiva resulta em `503` ou omissão da ação na consulta principal, jamais criação otimista de link de ação; a resposta do acompanhamento exige suas fontes necessárias.

| Cenário | Recebe confirmação? | Recebe liberação? |
|---|---|---|
| Gestor da prefeitura, compra confirmada e entrega agendada | Não | Não |
| Escola vinculada, compra confirmada e entrega agendada | Sim, apenas no portal | Não |
| Escola vinculada, entrega já recebida/cancelada | Não | Não |
| Outra escola ou produtor de outra compra | Resposta `403`; sem representação | Resposta `403` |
| Produtor da compra, confirmada | Não | Não |
| Gestor/produtor autorizado, compra recebida e liberação registrada | Não | Sim |
| Compra pendente ou cancelada | Não | Não |

Exemplo do link de ação no portal da escola:

```json
{
  "confirmar-recebimento": {
    "href": "/prefeitura/api/v1/entregas/00000015-0000-4000-8000-000000000001/recebimentos",
    "method": "POST"
  }
}
```

O cliente envia `{}` e `Idempotency-Key` no POST. O servidor gera ator e instante. Recebimento e `EntregaRecebida` são persistidos na mesma transação local de Entregas; a atualização de Compra e liberação ocorre depois, via consumidor. Repetição não autoriza um segundo recebimento ou pagamento.

## 6. Idempotência, erro e compatibilidade

Valem os [padrões REST](openapi/README.md): erro com quatro campos, UUID, valores decimais exatos, controle de versão e chaves HTTP distintas de IDs de mensagem/SAGA. O BFF preserva a chave em retransmissões para a mesma operação interna e não divide uma ação do cliente em várias escritas independentes.

O BFF não memoriza uma resposta de escrita antes de o domínio concluir a transação. Depois de uma perda de resposta, o reenvio da mesma chave recupera o resultado original; o cliente usa GET para consultar o estado atual. Uma resposta idempotente antiga não é reapresentada como estado novo. `Location` é reescrita junto do resultado.

Os BFFs usam seus prefixos `/api/v1` e versões documentais próprias. Compras mudou `info.version` para 1.1.0 pela representação HATEOAS prevista no projeto, sem alterar nome de estado ou caminho. Clientes que validam respostas com schema fechado precisam atualizar seu contrato ao receber `_links`; isso exige atualizar os consumidores afetados.

## 7. Cobertura e alternativas

| Tema | Evidência |
|---|---|
| Gateway | Rotas, verificação JWT delegada, duas fases de limite, headers/TLS/CORS, configurações e alternativas |
| BFFs | Dois OpenAPI externos, dashboard/inicio, operações específicas, ordenação/página versus cursor e sincronização, formatos diferentes |
| HATEOAS | Responsabilidades Compras/BFF, schemas `_links`, matriz estado/papel/vínculo e exemplos condicionais |
| Validação | [Validação dos seis contratos](openapi/VALIDACAO.md) e [ADR 0007](../adr/0007-acesso-gateway-bffs.md) |

| Alternativa | Avaliação |
|---|---|
| Gateway agrega os quatro serviços | Mistura entrada/autenticação com apresentação e necessidades dos clientes |
| Um BFF genérico | Obriga celular a receber payload/consulta próprios do portal ou cria condicionais por cliente no mesmo contrato |
| Clientes acessam domínio diretamente | Expõe serviços internos, aumenta chamadas móveis e duplica composição/autenticação |
| Envoy com `jwt_authn` | Alternativa com validação JWT integrada; configuração diferente da referência NGINX já escolhida |
| Kong ou Traefik/ForwardAuth | Alternativas viáveis, mas acrescentam outro produto ou convenções sem necessidade identificada nesta etapa |
| `limit_req` usando claim antes de `auth_request` | Não garante chave autenticada na fase em que o limite é aplicado; escolhido segundo salto privado |
| Inventar cursor incremental no serviço | Acrescentaria mecanismos de consulta e persistência aos serviços; escolhido cache de observação no BFF, com limites explícitos |

## 8. Referências técnicas

- [NGINX auth_request](https://nginx.org/en/docs/http/ngx_http_auth_request_module.html): subrequests de autorização e códigos aceitos.
- [NGINX proxy_pass](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass): substituição de prefixo quando uma URI é informada.
- [NGINX limit_req](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html): limites por chave.
- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html): ETag, If-None-Match, 304 e semântica HTTP.
- [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519.html) e [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html): claims e validação de JWT.

Taxas, TTLs, limites de composição, cache técnico e regras de payload são escolhas propostas do CampoConecta. As regras de integração propostas nos ADRs precisam ser confirmadas antes da implementação.
