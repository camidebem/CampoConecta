# ADR 0007 — Acesso por NGINX e dois BFFs

- **Status:** proposto.
- **Data:** 2026-10-20.
- **Relacionados:** [gateway e BFFs](../parte2/04-gateway-bffs.md), [conciliações ADR 0006](0006-conciliacao-contratos-rest.md), [índice dos contratos](../parte2/openapi/README.md).

## Contexto

Dois clientes acessam quatro serviços com bancos exclusivos. O portal precisa supervisionar editais, homologar planos e confirmar entregas; o aplicativo atende produtores em rede móvel e precisa de consultas compactas. A arquitetura usa NGINX com `auth_request`, um BFF por cliente e HATEOAS com responsabilidades divididas.

Este ADR detalha o acesso às APIs e a apresentação por cliente. Os componentes ainda não estão implantados.

## Decisão proposta

1. Entrada única HTTPS no gateway, com prefixos `/prefeitura/api/v1` e `/produtor/api/v1`. Somente `/health` e preflights conhecidos dispensam autenticação; `/_auth` é interno.
2. NGINX delega validação JWT e compatibilidade de papel/prefixo a `authn-verify`, sem banco. Headers de identidade externos são substituídos; Bearer e correlação são propagados.
3. Gateway limita por IP antes da autenticação e por identidade em um segundo listener somente loopback, após a autenticação. Isso evita usar variáveis de claims ainda não preenchidas na fase de limite do primeiro salto.
4. BFF prefeitura agrega Editais, Compras e Entregas; BFF produtor agrega os quatro serviços. Nenhum acessa banco de domínio, aplica reserva ou publica comando de SAGA para substituir uma escrita do dono.
5. Portal oferece dashboard, página de até 50 itens, filtros/ordenação enumerados e payload aninhado. Aplicativo oferece inicio, até 10 registros por cursor, compra achatada, ETag e mudanças observadas pelo BFF.
6. Cache técnico móvel é volátil e isolado por ator/vínculo/filtros. Cursor válido por dez minutos; histórico observado por trinta. Não há promessa de replay de cada evento ou sincronização baseada em timestamp de escrita que o domínio ainda não expõe. Perda de cache requer sincronização completa com `410`.
7. Compras fornece links de seus próprios recursos; BFF reescreve prefixos e acrescenta edital/entrega. Só escola vinculada com entrega agendada recebe `confirmar-recebimento`, e Entregas revalida a ação na escrita. Liberação é exposta apenas a gestor/produtor autorizados quando registrada.
8. Escritas preservam JWT, versão, chave idempotente, corpo e resultado do serviço. Não há retry automático de escrita no gateway nem composição de várias escritas sem processo de negócio definido.

## Alternativas consideradas

| Alternativa | Motivo da escolha atual |
|---|---|
| Gateway agregador | Composição de payload pertence ao cliente e ficaria acoplada à borda |
| Um único BFF | Necessidades de rede, volume, ações e paginação são distintas |
| Expor diretamente quatro APIs | Aumentaria o acoplamento dos clientes e abriria rotas internas |
| Envoy, Kong ou Traefik | Viáveis; NGINX preserva a escolha de referência e torna rotas explícitas, com verificação delegada |
| JWT decodificado sem validar assinatura | Não autentica emissor nem integridade das claims |
| Limite por token bruto fornecido pelo cliente | Tokens diferentes do mesmo ator contornariam o limite; não é a identidade validada |
| Novo banco de negócio no BFF para resolver sincronização | Duplicaria autoridade de dados; escolhido cache técnico reconstruível por APIs |
| Ordenação/cursor por SQL direto | Violaria propriedade e isolamento dos bancos |

## Consequências

**Benefícios:** clientes têm contratos específicos, APIs de domínio permanecem internas, regras decisivas continuam nos donos e HATEOAS expressa ações permitidas sem dispensar autorização. Os seis contratos podem ser validados de forma independente.

**Custos e limites:** dois BFFs exigem manutenção e validação separadas. O segundo salto adiciona um encaminhamento local. Cache móvel precisa de expiração e estratégia de réplica. Composições percorrem páginas e podem custar muitas chamadas; limite de 10.000 registros evita trabalho ilimitado, mas não substitui medição. A versão inicial não oferece linha do tempo HTTP nem log incremental completo de domínio.

As taxas, TTLs e timeouts são propostas não medidas. A lacuna de vínculo institucional em Entregas e a revisão de campos compartilhados permanecem no ADR 0006. `_links` é mudança de representação prevista no projeto, mas clientes com schema fechado devem atualizar o contrato antes da integração.

## Validação e revisão

Sintaxe/referências OpenAPI, exemplos, mapeamento de rotas e configuração NGINX são registrados em [VALIDACAO.md](../parte2/openapi/VALIDACAO.md). Não constituem teste de sistema em execução.

A revisão deve conferir compatibilidade dos clientes, autorização por recurso e consistência entre contratos, dados e mensagens. Mudanças precisam identificar consumidores afetados e atualizar os exemplos correspondentes.
