"""Valida o gateway, authn-verify e os dois BFFs em execução.

Uso: py -3 scripts/verificar-borda.py
"""

import json
import urllib.error
import urllib.request


BASE = "http://127.0.0.1:8080"


def requisicao(caminho: str, metodo: str = "GET", corpo: dict | None = None, token: str | None = None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    headers = {"Accept": "application/json"}
    if dados is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    requisicao_http = urllib.request.Request(
        f"{BASE}{caminho}",
        data=dados,
        headers=headers,
        method=metodo,
    )
    try:
        with urllib.request.urlopen(requisicao_http, timeout=5) as resposta:
            corpo_resposta = resposta.read()
            return resposta.status, json.loads(corpo_resposta) if corpo_resposta else {}
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read()) if exc.headers.get("Content-Type", "").startswith("application/json") else {}


def token(papel: str, vinculo: str):
    corpo = {"sub": f"teste-{papel}", "papel": papel}
    if papel in {"gestor", "escola"}:
        corpo["instituicaoId"] = vinculo
    else:
        corpo["produtorId"] = vinculo
    status, resposta = requisicao(
        f"/{'prefeitura' if papel in {'gestor', 'escola'} else 'produtor'}/token",
        "POST",
        corpo,
    )
    assert status == 200, (status, resposta)
    return resposta["token"]


def main():
    status, gateway = requisicao("/health")
    assert status == 200 and gateway["status"] == "ok"

    status, _ = requisicao("/prefeitura/api/v1/dashboard")
    assert status in {401, 403}, status
    status, _ = requisicao(
        "/prefeitura/api/v1/dashboard",
        token="jwt.invalido",
    )
    assert status in {401, 403}, status

    token_prefeitura = token("gestor", "00000000-0000-0000-0000-000000000001")
    status, prefeitura = requisicao(
        "/prefeitura/api/v1/dashboard",
        token=token_prefeitura,
    )
    assert status == 200 and prefeitura["cliente"] == "prefeitura"
    assert prefeitura["papel"] == "gestor"
    assert prefeitura["instituicaoId"] == "00000000-0000-0000-0000-000000000001"
    status, _ = requisicao(
        "/produtor/api/v1/inicio",
        token=token_prefeitura,
    )
    assert status in {401, 403}, status

    token_produtor = token("produtor", "00000000-0000-0000-0000-000000000002")
    status, produtor = requisicao(
        "/produtor/api/v1/inicio",
        token=token_produtor,
    )
    assert status == 200 and produtor["cliente"] == "produtor"
    assert produtor["produtorId"] == "00000000-0000-0000-0000-000000000002"
    status, _ = requisicao(
        "/prefeitura/api/v1/dashboard",
        token=token_produtor,
    )
    assert status in {401, 403}, status

    print("OK: gateway, JWT valido/invalido, papeis cruzados, dashboard da prefeitura e inicio do produtor.")


if __name__ == "__main__":
    main()
