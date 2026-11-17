# Serviços, redes e mensageria — frente do José

## Escopo entregue

Compras e Entregas seguem `servicos/editais`: FastAPI, Dockerfile multi-stage,
usuário sem privilégios, migrações com advisory lock, pool limitado,
`X-Correlation-Id`, erros padronizados e idempotência transacional.
Os serviços usam os bancos `pg-compras` e `pg-entregas` que já existiam no Compose.

| Serviço | Operação | Comportamento |
|---|---|---|
| Compras | `POST /api/v1/propostas` | Consulta edital, item, oferta, produtor e escola via APIs; grava proposta e snapshots; responde `201` com `Location` |
| Compras | `GET /api/v1/propostas/{id}` | Consulta persistida; `404` se não existir |
| Entregas | `POST /api/v1/capacidades` | Grava janela futura e capacidade positiva; rejeita sobreposição na mesma escola |
| Entregas | `GET /api/v1/capacidades/{id}` | Consulta persistida; `404` se não existir |
| Ambos | `GET /health` | `200` quando o próprio banco responde; `503` em falha |

Propostas exigem edital `PUBLICADO`, oferta ativa, escola/produtor ativos e
produto/unidade compatíveis. A consulta não reserva saldo. Falhas de dependência
geram erro sem persistir proposta nem resultado de sucesso na idempotência.
Reenvios já concluídos recuperam a resposta sem consultar as dependências.

Capacidades usam intervalos `[inicio, fim)`: janelas adjacentes são aceitas.
Um `pg_advisory_xact_lock` por escola serializa a verificação e a inserção entre
réplicas. A transação da chave idempotente inclui a capacidade. Após a janela
começar, o reenvio da mesma operação ainda pode recuperar a resposta original.

## Topologia

| Componente | Redes |
|---|---|
| Cada serviço de domínio | `aplicacao`, `mensageria`, `dados-<serviço>` |
| Cada PostgreSQL | somente `dados-<serviço>`, interna |
| RabbitMQ | somente `mensageria`, interna |
| BFFs, após integração do Daniel | `borda`, `aplicacao` |
| Gateway, após integração do Daniel | somente `borda` |

Os serviços participam de `mensageria` porque serão os participantes da SAGA.
Compartilhar `aplicacao` não dá acesso a bancos: estes não participam dessa rede
e não publicam portas. A rede `borda` é declarada agora, mas só será criada pelo
Compose quando tiver participantes. Nenhum gateway/BFF fictício foi adicionado.

## RabbitMQ e persistência

- Imagem `rabbitmq:4.1-alpine`, hostname fixo `rabbitmq` e volume
  `rabbitmq-dados:/var/lib/rabbitmq` para manter identidade e dados do nó.
- Usuário, senha e vhost vêm do `.env`; a URL AMQP é composta no Compose e
  recebida pelos serviços. Não há credenciais de execução versionadas.
- Healthcheck verifica aplicação em execução e conectividade dos listeners.
  Os serviços aguardam o broker saudável antes de iniciar.
- O broker não publica portas no host. Ainda não há consumidores, filas de
  negócio ou relay; esses componentes pertencem à Parte 4.

A imagem PostgreSQL continua comum às quatro instâncias. O build está declarado
somente em `pg-editais`; os demais reutilizam a mesma tag local. Isso evita a
disputa de quatro exports simultâneos para a mesma imagem no containerd.
O comando de subida continua sendo `docker compose up -d --build`.

O healthcheck do PostgreSQL usa TCP em `127.0.0.1`, disponível somente no
servidor definitivo, após os scripts de inicialização. Isso impede iniciar
aplicações contra o servidor temporário que o entrypoint usa por socket local.
O período inicial de 60 segundos acomoda a criação dos volumes na primeira subida.

## Limites de integração

Esta frente preserva a limitação do modelo base: serviços ainda não validam JWT
nem autorizam recursos por usuário. Em Compras, `produtorId` é obtido da oferta
consultada, mas isso não prova que o solicitante é aquele produtor. Antes de
expor essa operação pelo BFF, é necessário validar o vínculo com a identidade.
Entregas ainda não verifica o vínculo institucional de `escolaId`, pendente no
ADR 0006. `JWT_SECRET` está reservado no `.env.example` para a frente de borda.

As operações de proposta não criam Compra; homologação, reserva, agendamento,
recebimento e pagamento continuam fora desta implementação. Não há
`POST /compras` nem escrita direta em banco de outro serviço.

O script de integração cria um edital de demonstração e usa o serviço dono
para publicá-lo por SQL, já que a API de publicação ainda não existe. Essa
fixture não faz parte das migrações nem é executada durante a subida normal.

## Verificações reproduzíveis

```sh
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
python3 scripts/verificar-parte3.py
python3 scripts/verificar-isolamento.py --sonda
```

O verificador de integração cria registros novos e os mantém para inspeção;
não limpa volumes ou para serviços. Verifica referências, persistência por GET,
idempotência, rejeições, acesso AMQP, concorrência e redes declaradas.

O verificador de isolamento testa quatro controles positivos (dono → banco),
quatro APIs alcançáveis, DNS dos bancos indisponível e TCP direto bloqueado.
O modo `--sonda` é uma prova preliminar. A prova a partir do BFF real exige
`--bff bff-prefeitura` ou `--bff bff-produtor` após a integração correspondente.
