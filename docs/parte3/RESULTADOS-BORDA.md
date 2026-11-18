# Resultados reproduzidos da borda

Data da execução: 17/11/2026  
Branch validada: `feat/borda-bffs`  
Ambiente: Docker Desktop com Docker Engine 29.7.2 e Docker Compose v2

Este documento registra os resultados obtidos na implementação da borda.
Os testes abaixo foram executados antes da apresentação e não precisam ser
reexecutados ao vivo.

## Ambiente

O Compose foi iniciado com todos os componentes da aplicação. A borda ficou
disponível em `127.0.0.1:8080`, com os seguintes componentes saudáveis:

- `gateway`
- `authn-verify`
- `bff-prefeitura`
- `bff-produtor`
- `editais`
- `ofertas`
- `compras`
- `entregas`
- quatro PostgreSQL
- RabbitMQ

Resultado: os quatro bancos, os quatro microsserviços, o RabbitMQ e os quatro
componentes da borda apareceram como `healthy`.

## Gateway e healthcheck

O endpoint público do gateway respondeu:

```text
status  servico
------  -------
ok      gateway
```

Isso confirma que o único publicador externo HTTP da borda está em execução.

## Fluxo ponta a ponta

O script `scripts/verificar-borda.py` foi executado e retornou:

```text
OK: gateway, JWT valido/invalido, papeis cruzados,
dashboard da prefeitura e inicio do produtor.
```

Os resultados verificados pelo script foram:

| Caso | Resultado |
|---|---|
| Requisição sem JWT no dashboard | Bloqueada |
| JWT inválido no dashboard | Bloqueada |
| JWT gestor no `/prefeitura/api/v1/dashboard` | Permitida |
| Claim de prefeitura propagada ao BFF | Confirmada |
| JWT gestor no `/produtor/api/v1/inicio` | Bloqueada |
| JWT produtor no `/produtor/api/v1/inicio` | Permitida |
| Claim de produtor propagada ao BFF | Confirmada |
| JWT produtor no `/prefeitura/api/v1/dashboard` | Bloqueada |

As respostas distintas retornaram:

```text
PREFEITURA= prefeitura / gestor
PRODUTOR= produtor / <produtorId> / <quantidade de ofertas ativas>
```

## Isolamento dos bancos

O script `scripts/verificar-isolamento.py --bff bff-prefeitura` retornou:

- controle positivo: cada microsserviço acessa seu próprio banco;
- APIs `editais`, `ofertas`, `compras` e `entregas` acessíveis pelo BFF;
- DNS de `pg-editais` isolado;
- TCP direto de `pg-editais` bloqueado;
- DNS de `pg-ofertas` isolado;
- TCP direto de `pg-ofertas` bloqueado;
- DNS de `pg-compras` isolado;
- TCP direto de `pg-compras` bloqueado;
- DNS de `pg-entregas` isolado;
- TCP direto de `pg-entregas` bloqueado;
- isolamento confirmado a partir de `bff-prefeitura`.

O mesmo procedimento foi executado com
`scripts/verificar-isolamento.py --bff bff-produtor` e confirmou isolamento
equivalente a partir de `bff-produtor`.

## Resposta para o vídeo

Durante a apresentação, o resultado pode ser descrito assim:

> A borda foi executada e validada. O gateway ficou saudável na porta local,
> o JWT foi emitido e validado em ambos os papéis, rotas cruzadas e tokens
> inválidos foram bloqueados, o dashboard e o início responderam por seus
> respectivos clientes e os dois BFFs não conseguiram resolver nem acessar
> diretamente os bancos de dados.
