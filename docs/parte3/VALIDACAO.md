# Validação da frente de serviços, redes e mensageria

Data: 17/11/2026. Ambiente: Ubuntu no WSL 2, Docker Engine 29.1.3 e
Docker Compose 2.40.3. As credenciais de execução foram geradas no `.env` local,
ignorado pelo Git. Nenhuma credencial é incluída neste relatório.

## Resultados reproduzidos

| Verificação | Resultado |
|---|---|
| `docker compose config --quiet` | Configuração válida |
| `docker compose up -d --build --wait --wait-timeout 180` | Subida concluída |
| `docker compose ps` | Treze contêineres `healthy`, gateway publica somente `127.0.0.1:8080` |
| Compilação Python com `compileall` | Sem erros nos dois novos serviços e scripts |
| Healthchecks das APIs | Quatro respostas `200`, consultando o banco do próprio serviço |
| RabbitMQ | Aplicação em execução; conexão TCP em 5672 a partir dos quatro serviços |
| Propostas | Criação e consulta persistida; IDs e snapshot correspondentes às referências consultadas |
| Validações de proposta | Edital rascunho e unidade incompatível rejeitados com `409`; chave ausente com `400`; recurso ausente com `404` |
| Idempotência | Reenvio idêntico recupera corpo/ID originais e sinaliza replay; chave reutilizada com outro conteúdo gera `409` |
| Capacidades | Criação e consulta persistida; quantidade reservada inicial `0.00` |
| Intervalos | Sobreposição rejeitada; janela adjacente aceita; janela passada/invertida rejeitada |
| Decimais | Zero, negativo, três casas e número JSON rejeitados na capacidade |
| Concorrência logística | Duas requisições simultâneas para a mesma escola/janela resultam em um `201` e um `409` |
| Isolamento — controle positivo | Cada serviço consegue executar `SELECT 1` no próprio banco |
| Isolamento — sonda em `aplicacao` | Quatro APIs acessíveis; quatro nomes de banco não resolvidos; TCP direto aos quatro IPs bloqueado |
| `git diff --check` | Sem erros de whitespace |

Comandos dos testes:

```sh
python3 scripts/verificar-parte3.py
python3 scripts/verificar-isolamento.py --sonda
```

O verificador de APIs mantém os dados criados para inspeção. A publicação por SQL
é uma fixture explícita no banco de Editais, executada somente para o edital
criado pelo próprio teste. A subida normal não cria dados de demonstração.

## Limites da evidência

O modo `--sonda` verifica a segmentação de rede. O script também oferece
`--bff bff-prefeitura` e `--bff bff-produtor` para executar a mesma prova
dentro dos componentes reais da borda.

O JWT de desenvolvimento, os BFFs e o gateway desta frente foram validados em
execução. SAGA, consumidores, outbox e CQRS continuam fora desta etapa. Não
devem ser confundidos com controles já implementados nesta frente. O healthcheck de
cada serviço de domínio mede o próprio banco; não afirma disponibilidade de
todas as dependências HTTP nem processamento de mensagens.

O [gravador](../../scripts/gravar-demonstracao.py) registra as saídas reais em um
projeto separado, com volumes novos e imagens possivelmente em cache. Evidências
locais ficam em `evidencias.local/`, sem entrar no Git. A gravação preliminar
identifica explicitamente o uso de sonda.

### Validação da borda

Executar após a subida completa:

```sh
docker compose up -d --build --wait --wait-timeout 240
py -3 scripts/verificar-borda.py
```
