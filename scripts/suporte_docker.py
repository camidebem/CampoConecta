"""Utilitários dos verificadores; executam o Compose da raiz do repositório."""

import json
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def docker(*argumentos: str, entrada: str | None = None) -> str:
    resultado = subprocess.run(
        ["docker", *argumentos], cwd=RAIZ, input=entrada,
        text=True, capture_output=True, check=True,
    )
    return resultado.stdout


def compose(*argumentos: str, entrada: str | None = None) -> str:
    return docker("compose", *argumentos, entrada=entrada)


HTTP = """
import json, sys, urllib.request, urllib.error
p = json.load(sys.stdin)
req = urllib.request.Request('http://127.0.0.1:8000' + p['caminho'],
    data=None if p['corpo'] is None else json.dumps(p['corpo']).encode(),
    headers=p['headers'], method=p['metodo'])
try:
    resposta = urllib.request.urlopen(req, timeout=15)
except urllib.error.HTTPError as exc:
    resposta = exc
with resposta:
    print(json.dumps({'status': resposta.status, 'headers': {k.lower(): v for k, v in resposta.headers.items()},
                      'corpo': json.load(resposta)}))
"""


def api(servico: str, metodo: str, caminho: str, corpo=None, chave=None) -> dict:
    headers = {"Content-Type": "application/json"}
    if chave:
        headers["Idempotency-Key"] = chave
    return json.loads(compose("exec", "-T", servico, "python", "-c", HTTP, entrada=json.dumps({
        "metodo": metodo, "caminho": caminho, "corpo": corpo, "headers": headers,
    })))


def sql(servico: str, comando: str, parametros: list) -> None:
    codigo = """
import json, os, sys, psycopg
p = json.load(sys.stdin)
with psycopg.connect(os.environ['DATABASE_URL']) as conn:
    conn.execute(p['sql'], p['parametros'])
"""
    compose("exec", "-T", servico, "python", "-c", codigo,
            entrada=json.dumps({"sql": comando, "parametros": parametros}))
