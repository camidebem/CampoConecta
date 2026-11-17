"""Prova DNS + TCP dos quatro bancos, com controle positivo das APIs.

python3 scripts/verificar-isolamento.py --bff bff-prefeitura
python3 scripts/verificar-isolamento.py --sonda  # preliminar, enquanto o BFF não existe
"""

import argparse
import json

from suporte_docker import compose, docker

CODIGO = """
import json, socket, sys, urllib.request
alvos = json.loads(sys.argv[1])
for servico in ('editais', 'ofertas', 'compras', 'entregas'):
    with urllib.request.urlopen('http://' + servico + ':8000/health', timeout=5) as resposta:
        assert resposta.status == 200
    print('OK: API ' + servico + ' acessível', flush=True)
for alvo in alvos:
    try:
        socket.getaddrinfo(alvo['nome'], 5432)
    except socket.gaierror:
        print('OK: DNS de ' + alvo['nome'] + ' isolado', flush=True)
    else:
        raise AssertionError('Banco resolvível: ' + alvo['nome'])
    try:
        conexao = socket.create_connection((alvo['ip'], 5432), timeout=1)
    except OSError:
        print('OK: TCP direto de ' + alvo['nome'] + ' bloqueado', flush=True)
    else:
        conexao.close()
        raise AssertionError('Banco acessível pelo IP: ' + alvo['nome'])
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--bff", choices=["bff-prefeitura", "bff-produtor"])
    modo.add_argument("--sonda", action="store_true")
    args = parser.parse_args()
    config = json.loads(compose("config", "--format", "json"))
    alvos = []
    for servico in ("editais", "ofertas", "compras", "entregas"):
        # Controle positivo: o dono usa sua credencial e alcança o próprio banco.
        compose("exec", "-T", servico, "python", "-c",
                "import os, psycopg; c = psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=3); "
                "assert c.execute('SELECT 1').fetchone()[0] == 1; c.close()")
        banco = f"pg-{servico}"
        container = compose("ps", "-q", banco).strip()
        assert container, f"Banco não está em execução: {banco}"
        redes = json.loads(docker("inspect", "--format", "{{json .NetworkSettings.Networks}}", container))
        rede = config["networks"][f"dados-{servico}"]["name"]
        alvos.append({"nome": banco, "ip": redes[rede]["IPAddress"]})
    print("OK: cada serviço alcança seu próprio banco.", flush=True)

    if args.bff:
        assert args.bff in config["services"], "BFF ainda não integrado ao Compose. Use --sonda para a prova preliminar."
        redes = set(config["services"][args.bff]["networks"])
        assert redes == {"borda", "aplicacao"}, f"Redes inesperadas no BFF: {redes}"
        resultado = compose("exec", "-T", args.bff, "python", "-c", CODIGO, json.dumps(alvos))
        print(resultado, end="")
        print(f"Isolamento comprovado a partir de {args.bff}.")
    else:
        # Sonda descartável sem credenciais e sem nenhuma rede de dados.
        # borda ainda não tem participantes; a aplicação é a rede compartilhada
        # por onde o BFF alcançará os serviços. Não se cria um BFF fictício.
        rede = config["networks"]["aplicacao"]["name"]
        imagem = config["services"]["compras"]["image"]
        resultado = docker("run", "--rm", "--network", rede, "--entrypoint", "python",
                           imagem, "-c", CODIGO, json.dumps(alvos))
        print(resultado, end="")
        print("Prova preliminar com sonda na rede aplicacao. Repetir com --bff após integrar a borda.")


if __name__ == "__main__":
    main()
