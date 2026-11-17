"""Grava saídas reais no formato asciinema v2, sem mostrar configuração sensível.

Uso: python3 scripts/gravar-demonstracao.py [--bff bff-prefeitura]
Usa um projeto Docker novo, mantém volumes e encerra os contêineres ao terminar.
Sem --bff, identifica a prova como preliminar com sonda.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

from suporte_docker import RAIZ


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bff", choices=["bff-prefeitura", "bff-produtor"])
    args = parser.parse_args()
    identificador = datetime.now().strftime("%Y%m%d-%H%M%S")
    projeto = f"campoconecta-video-{identificador}"
    pasta = RAIZ / "evidencias.local" / identificador
    pasta.mkdir(parents=True, exist_ok=False)
    ambiente = dict(os.environ, COMPOSE_PROJECT_NAME=projeto, COMPOSE_ANSI="never", BUILDKIT_PROGRESS="plain")
    comandos = [
        ["docker", "compose", "config", "--quiet"],
        ["docker", "compose", "up", "-d", "--build", "--wait", "--wait-timeout", "180"],
        ["docker", "compose", "ps"],
        [sys.executable, "scripts/verificar-parte3.py"],
        [sys.executable, "scripts/verificar-isolamento.py", *(["--bff", args.bff] if args.bff else ["--sonda"])],
    ]
    inicio = time.monotonic()
    with (pasta / "demonstracao.cast").open("w", encoding="utf-8") as cast, \
            (pasta / "transcricao.txt").open("w", encoding="utf-8") as transcricao:
        cast.write(json.dumps({"version": 2, "width": 140, "height": 40, "timestamp": int(time.time()),
                               "title": "CampoConecta - Parte 3", "idle_time_limit": 1}) + "\n")

        def registrar(texto):
            print(texto, end="", flush=True)
            transcricao.write(texto)
            cast.write(json.dumps([round(time.monotonic() - inicio, 3), "o", texto], ensure_ascii=False) + "\n")
            cast.flush()

        def executar(comando):
            registrar("\n$ " + " ".join(comando) + "\n")
            with subprocess.Popen(comando, cwd=RAIZ, env=ambiente, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1) as processo:
                for linha in processo.stdout:
                    registrar(linha)
                if processo.wait():
                    raise RuntimeError("A demonstração falhou; consulte a transcrição.")

        registrar(f"Projeto novo: {projeto}. Volumes novos; imagens podem estar em cache.\n")
        registrar("Modo: BFF real.\n" if args.bff else "Modo: sonda preliminar; BFFs ainda não integrados.\n")
        try:
            for comando in comandos:
                executar(comando)
        finally:
            executar(["docker", "compose", "down"])
    print(f"Gravação e transcrição: {pasta}")


if __name__ == "__main__":
    main()
