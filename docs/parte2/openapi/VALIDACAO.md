# Validação dos contratos e do gateway

**Data:** 20/10/2026. **Branch de trabalho:** `docs/apis-bffs`. Este relatório descreve checagens de artefatos, sem afirmar implementação, implantação ou integração já realizada.

## 1. Artefatos

| Artefato | Objetivo |
|---|---|
| [Editais](editais.openapi.json), [Ofertas](ofertas.openapi.json), [Compras](compras.openapi.json), [Entregas](entregas.openapi.json) | Quatro APIs de domínio, com cadastro, consulta e transições de estado |
| [BFF prefeitura](bff-prefeitura.openapi.json), [BFF produtor](bff-produtor.openapi.json) | Acesso específico de cada cliente, agregações e adaptação de payload |
| [Gateway e BFFs](../04-gateway-bffs.md) | Rotas, responsabilidades, exemplos e HATEOAS |
| [NGINX](../gateway/nginx/nginx.conf) e includes | Configuração documental de borda |
| [ADR 0007](../../adr/0007-acesso-gateway-bffs.md) | Contexto, alternativas e consequências da proposta de acesso |

Compras passa a `info.version: 1.1.0` pela adição de `_links`, prevista no projeto. Os outros contratos mantêm versão documental 1.0.0. Todos usam OpenAPI 3.1.0. Revisão de consumidores com schemas fechados permanece necessária.

## 2. Checagens e resultados

| Checagem | Ferramenta/evidência | Resultado |
|---|---|---|
| Sintaxe OpenAPI e referências | Redocly CLI 2.8.0 nos seis contratos | Sem erros ou avisos na versão final |
| Exemplos conforme schemas | Ajv com JSON Schema 2020-12 e ajv-formats, em verificação local temporária | 716 exemplos de schemas, requisições, respostas e exemplos nomeados válidos; UUIDs/datas conferidos |
| Cobertura de domínio | Script estático comparando a matriz de operações REST por serviço | As 37 operações da matriz estão presentes; duas consultas adicionais permitem localizar planos e capacidades |
| Operações nos seis contratos | [verificar-contratos.cjs](verificar-contratos.cjs) | 90 operações, com operationId único, papéis/vínculos documentados e chaves nas escritas |
| Origem de operações dos BFFs | Mesmo script, contra método/caminho dos quatro contratos internos | 65 referências de origem válidas; BFF prefeitura não consulta Ofertas |
| HATEOAS de exemplos | Mesmo script: prefixo, método e existência da operação de destino | 79 links verificados; recebimento apenas no BFF prefeitura, exemplos de escola/gestor/produtor distintos |
| Sem criação pública de Compra/reservas | Script e revisão da superfície | Compra nasce só da homologação; escrita de reservas e agendamento permanece na SAGA |
| Cache HTTP móvel | Script e revisão de contratos | 304 sem corpo, If-None-Match documentado e respostas privadas; paginação por cursor separada do domínio |
| Casos negativos de schema | Ajv | Rejeitados: quantidade numérica, zero, negativa, três casas; ajuste de item sem ação, com duas ações ou com excluir=false |
| Sintaxe NGINX | Binário oficial Windows NGINX 1.28.3, com `auth_request`, somente `nginx -t` | Sintaxe e teste de configuração concluídos com sucesso em cópia temporária |

O teste NGINX substituiu **somente na cópia temporária** os três nomes DNS de serviços por endereços loopback e gerou um certificado autoassinado de um dia para satisfazer a leitura de TLS. Foram criados diretórios temporários de logs e arquivos de trabalho. Não foi iniciado servidor, alterado DNS/hosts do sistema, instalado certificado nem incluída chave privada no repositório. O teste não comprova conectividade com BFFs, OIDC ou serviços reais.

## 3. Reprodução

Na raiz do repositório, com Node.js e npm:

```powershell
npm exec --yes --package=@redocly/cli@2.8.0 -- redocly lint docs/parte2/openapi/editais.openapi.json docs/parte2/openapi/ofertas.openapi.json docs/parte2/openapi/compras.openapi.json docs/parte2/openapi/entregas.openapi.json docs/parte2/openapi/bff-prefeitura.openapi.json docs/parte2/openapi/bff-produtor.openapi.json --extends minimal
node docs/parte2/openapi/verificar-contratos.cjs
```

O primeiro comando usa cache npm e valida os seis documentos com ferramenta OpenAPI. O segundo é uma checagem complementar sem dependências: referências locais, cobertura, segurança documentada, origens e links dos exemplos. Não substitui validação OpenAPI ou testes de autorização em execução.

Com NGINX compilado com SSL e auth_request, preparar prefixo temporário com as quatro configurações, `logs/`, `temp/`, certificado/chave de teste e nomes internos resolvíveis. Então executar somente:

```text
nginx -t -p <prefixo-absoluto-com-barra-final>/ -c nginx.conf
```

Não executar a configuração de exemplo como ambiente de produção: origem CORS, certificados, nomes, taxas e portas são referências a ajustar na implantação. Os números de taxa/latência/TTL não foram medidos.

## 4. Limites e integração

- Autorização real depende do provedor, verificador, BFFs e serviços ainda não implementados. Testes futuros precisam tentar acesso de outra escola/produtor, headers falsos, JWT inválido e respostas tardias.
- A condição de HATEOAS não concede direito: Entregas deve revalidar papel, vínculo, estado e idempotência no POST, mesmo com link válido.
- Cursor incremental é cache de observação, não log de domínio. Reinício, expiração, mudanças durante varreduras e múltiplas réplicas precisam dos comportamentos descritos no contrato, mais testes de implementação.
- Os serviços atuais não oferecem histórico HTTP de transições nem snapshot global de consultas. Os BFFs não inventam esses dados.
- [ADR 0006](../../adr/0006-conciliacao-contratos-rest.md) continua proposto: escola do item, preço/total, critérios, vínculos institucionais e outras conciliações exigem revisão dos componentes afetados.
- [ADR 0007](../../adr/0007-acesso-gateway-bffs.md) registra decisões propostas de acesso e apresentação.

Antes da implementação, revisar as dependências de dados e mensagens e conferir os exemplos de ponta a ponta.
