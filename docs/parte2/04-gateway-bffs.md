# Gateway, BFFs e HATEOAS

Configuração proposta de acesso às APIs do CampoConecta. Os componentes ainda não estão implantados.

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

Certificados em `certs/tls.crt` e `certs/tls.key`, DNS dos upstreams, diretórios `logs/` e `temp/` e módulos precisam existir no ambiente futuro. Nenhum certificado/chave privada foi incluído no repositório. Antes de iniciar, validar com `nginx -t -p <prefixo-absoluto>/ -c nginx.conf`. O teste de sintaxe não comprova integração com os serviços.
