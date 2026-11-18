# Vídeo — subida do zero e isolamento

## Preparação

Use uma cópia local com `.env` configurado, Docker/Compose v2 e Python 3.10+.
Não mostre o conteúdo do `.env`, `docker inspect` completo ou `docker compose config`
sem `--quiet`: esses comandos podem mostrar credenciais.

Para demonstrar volumes novos sem apagar os dados de desenvolvimento, use um
projeto separado. No PowerShell:

```powershell
$env:COMPOSE_PROJECT_NAME = 'campoconecta-video'
```

No Bash/WSL:

```sh
export COMPOSE_PROJECT_NAME=campoconecta-video
```

O nome precisa ainda não ter sido usado para que os volumes sejam novos. As
imagens podem estar em cache; declare isso na gravação. Os scripts respeitam a
mesma variável. Use o Compose principal, sem override que publique os serviços.

## Sequência sugerida (2–3 minutos)

1. Mostre a branch e o comando `git status --short`. Explique os quatro serviços,
   quatro bancos e o RabbitMQ, com volumes separados.
2. Execute a subida e mostre a criação dos volumes/contêineres:

   ```sh
   docker compose up -d --build --wait --wait-timeout 180
   docker compose ps
   ```

3. Confirme os nove componentes saudáveis desta frente. Depois da integração
   de borda, inclua gateway, verificador e BFFs na conferência.
4. Execute `python3 scripts/verificar-parte3.py`. Mostre os resultados de criação,
   consulta, idempotência e sobreposição. Explique a fixture de publicação do
   edital de teste; não existe publicação automática na subida.
5. **Com o BFF integrado**, execute:

   ```sh
   python3 scripts/verificar-isolamento.py --bff bff-prefeitura
   python3 scripts/verificar-isolamento.py --bff bff-produtor
   ```

   Mostre as APIs acessíveis, os bancos acessíveis aos próprios donos e os bancos
   bloqueados para o BFF por DNS e por conexão direta ao IP.
6. Mostre `docker compose down` e uma nova subida para explicar que os volumes
   persistem. Não use `down -v` na gravação com dados que devam ser preservados.

## Demonstração preliminar opcional

Antes da integração completa da borda, é possível usar
`python3 scripts/verificar-isolamento.py --sonda`. A sonda é um contêiner
descartável na rede `aplicacao`, sem credenciais de banco. Após a integração,
prefira a execução real com `--bff bff-prefeitura` ou `--bff bff-produtor`.

## Gravação reproduzível do terminal

```sh
python3 scripts/gravar-demonstracao.py
# Após integrar a borda:
python3 scripts/gravar-demonstracao.py --bff bff-prefeitura
```

O gravador executa os comandos em um projeto com nome novo, salva as saídas reais
em `evidencias.local/<data-hora>/demonstracao.cast` (asciinema v2) e
`transcricao.txt`, e encerra os contêineres preservando os volumes ao terminar.
O diretório de evidências é ignorado pelo Git. A gravação preliminar identifica
explicitamente o uso da sonda. Ela pode ser reproduzida com um player asciinema;
nenhum resultado é simulado pelo gravador.
