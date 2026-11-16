#!/usr/bin/env bash
# Compara o tamanho da imagem do serviço editais com 1 estágio vs multi-stage.
# Uso (na raiz do repositório, Git Bash/Linux/macOS):  bash scripts/medir-imagens.sh
set -euo pipefail

CTX=servicos/editais

echo ">> build multi-stage (Dockerfile)"
docker build -q -t campoconecta/editais:multi-stage "$CTX" >/dev/null

echo ">> build estágio único (Dockerfile.estagio-unico)"
docker build -q -f "$CTX/Dockerfile.estagio-unico" -t campoconecta/editais:estagio-unico "$CTX" >/dev/null

multi=$(docker image inspect -f '{{.Size}}' campoconecta/editais:multi-stage)
unico=$(docker image inspect -f '{{.Size}}' campoconecta/editais:estagio-unico)

echo
printf "%-16s %10s\n" "variante" "tamanho"
printf "%-16s %8d MB\n" "estagio-unico" $((unico / 1000000))
printf "%-16s %8d MB\n" "multi-stage" $((multi / 1000000))
echo "redução: $(( (unico - multi) / 1000000 )) MB ($(( 100 * (unico - multi) / unico ))%)"

echo
echo ">> o que existe só na imagem de estágio único:"
for img in estagio-unico multi-stage; do
  printf "%-16s gcc: %-4s  libpq-dev(pg_config): %s\n" "$img" \
    "$(docker run --rm --entrypoint sh campoconecta/editais:$img -c 'command -v gcc >/dev/null && echo sim || echo nao')" \
    "$(docker run --rm --entrypoint sh campoconecta/editais:$img -c 'command -v pg_config >/dev/null && echo sim || echo nao')"
done
