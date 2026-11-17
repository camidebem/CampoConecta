"""Integração real com os serviços em execução. Cria e mantém dados de demonstração.

Uso: python3 scripts/verificar-parte3.py (após docker compose up --wait).
Não apaga volumes, não para serviços e não imprime credenciais.
"""

import copy
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from suporte_docker import api, compose, sql


def chave() -> str:
    return str(uuid.uuid4())


def esperar(resposta: dict, status: int) -> dict:
    assert resposta["status"] == status, (status, resposta)
    return resposta["corpo"]


def criar(servico: str, caminho: str, corpo: dict) -> dict:
    return esperar(api(servico, "POST", caminho, corpo, chave()), 201)


def main():
    # Este JSON inclui configuração sensível: somente os campos estruturais são usados.
    config = json.loads(compose("config", "--format", "json"))
    # Compose omite redes sem participantes da configuração normalizada.
    # borda está reservada no YAML e aparecerá aqui após a integração dos BFFs.
    for nome in ("aplicacao", "mensageria"):
        assert nome in config["networks"]
    assert config["networks"]["mensageria"]["internal"]
    for servico in ("editais", "ofertas", "compras", "entregas"):
        redes = config["services"][servico]["networks"]
        assert set(redes) == {"aplicacao", "mensageria", f"dados-{servico}"}
        assert config["networks"][f"dados-{servico}"]["internal"]
        assert not config["services"][servico].get("ports")
        assert set(config["services"][f"pg-{servico}"]["networks"]) == {f"dados-{servico}"}
        assert not config["services"][f"pg-{servico}"].get("ports")
        esperar(api(servico, "GET", "/health"), 200)
    broker = config["services"]["rabbitmq"]
    assert not broker.get("ports") and set(broker["networks"]) == {"mensageria"}
    assert any(v["target"] == "/var/lib/rabbitmq" and v["type"] == "volume" for v in broker["volumes"])
    compose("exec", "-T", "rabbitmq", "rabbitmq-diagnostics", "-q", "check_running")
    for servico in ("editais", "ofertas", "compras", "entregas"):
        compose("exec", "-T", servico, "python", "-c",
                "import socket; socket.create_connection(('rabbitmq', 5672), timeout=3).close()")
    print("OK: quatro /health, bancos isolados na configuração e RabbitMQ acessível pelos quatro serviços.")

    prefeitura = criar("editais", "/api/v1/prefeituras", {
        "nome": "Prefeitura demonstração", "cnpj": str(uuid.uuid4().int)[:14],
    })
    escola = criar("editais", "/api/v1/escolas", {
        "prefeituraId": prefeitura["id"], "nome": "Escola demonstração",
        "endereco": {"logradouro": "Rua Exemplo", "numero": "1", "bairro": "Centro",
                     "municipio": "Lavras", "uf": "MG", "cep": "37200000"},
    })
    produtor = criar("ofertas", "/api/v1/produtores", {
        "nome": "Produtor demonstração", "documento": str(uuid.uuid4().int)[:11],
        "email": "demonstracao@example.com",
    })
    oferta = criar("ofertas", "/api/v1/ofertas", {
        "produtorId": produtor["id"], "produto": "Arroz",
        "quantidadeDisponivel": {"valor": "100.00", "unidade": "kg"},
    })
    inicio = datetime.now(timezone.utc) + timedelta(days=2)
    edital = criar("editais", "/api/v1/editais", {
        "prefeituraId": prefeitura["id"], "titulo": "Edital demonstração",
        "prazoEntrega": (inicio + timedelta(days=1)).isoformat(),
        "criterios": [{"codigo": "ORDEM_ENVIO", "ordem": "ASC", "parametros": {}}],
        "itens": [{"escolaId": escola["id"], "produto": "Arroz",
                   "quantidade": {"valor": "100.00", "unidade": "kg"}}],
    })
    proposta = {
        "editalId": edital["id"], "itemEditalId": edital["itens"][0]["id"], "ofertaId": oferta["id"],
        "quantidade": {"valor": "20.00", "unidade": "kg"},
        "precoUnitario": {"valor": "5.00", "moeda": "BRL"},
    }
    idempotencia = chave()
    esperar(api("compras", "POST", "/api/v1/propostas", proposta, idempotencia), 409)
    # Fixture explícita: Editais ainda não implementa publicação por HTTP.
    # Só o serviço dono altera seu banco e apenas o edital criado neste teste.
    sql("editais", "UPDATE edital SET status = 'PUBLICADO', versao = versao + 1 WHERE id = %s", [edital["id"]])
    primeira = api("compras", "POST", "/api/v1/propostas", proposta, idempotencia)
    gravada = esperar(primeira, 201)
    assert gravada["produtorId"] == produtor["id"] and gravada["status"] == "ENVIADA"
    assert primeira["headers"]["location"] == f"/api/v1/propostas/{gravada['id']}"
    repetida = api("compras", "POST", "/api/v1/propostas", proposta, idempotencia)
    assert esperar(repetida, 201) == gravada
    assert repetida["headers"]["idempotent-replayed"] == "true"
    assert esperar(api("compras", "GET", primeira["headers"]["location"]), 200) == gravada
    diferente = copy.deepcopy(proposta)
    diferente["quantidade"]["valor"] = "21.00"
    esperar(api("compras", "POST", "/api/v1/propostas", diferente, idempotencia), 409)
    diferente["quantidade"]["unidade"] = "litro"
    esperar(api("compras", "POST", "/api/v1/propostas", diferente, chave()), 409)
    esperar(api("compras", "POST", "/api/v1/propostas", proposta), 400)
    esperar(api("compras", "GET", f"/api/v1/propostas/{chave()}"), 404)
    print("OK: propostas persistidas, edital em rascunho rejeitado, unidade validada e repetição sem duplicação.")

    capacidade = {
        "escolaId": escola["id"],
        "janela": {"inicio": inicio.isoformat(), "fim": (inicio + timedelta(hours=2)).isoformat()},
        "capacidadeKg": "500.00",
    }
    idempotencia = chave()
    primeira = api("entregas", "POST", "/api/v1/capacidades", capacidade, idempotencia)
    gravada = esperar(primeira, 201)
    assert gravada["reservadoKg"] == "0.00" and gravada["versao"] == 1
    repetida = api("entregas", "POST", "/api/v1/capacidades", capacidade, idempotencia)
    assert esperar(repetida, 201) == gravada
    assert repetida["headers"]["idempotent-replayed"] == "true"
    assert esperar(api("entregas", "GET", primeira["headers"]["location"]), 200) == gravada
    esperar(api("entregas", "POST", "/api/v1/capacidades", capacidade, chave()), 409)
    adjacente = copy.deepcopy(capacidade)
    adjacente["janela"] = {"inicio": capacidade["janela"]["fim"], "fim": (inicio + timedelta(hours=3)).isoformat()}
    criar("entregas", "/api/v1/capacidades", adjacente)
    invalida = copy.deepcopy(capacidade)
    invalida["janela"]["fim"] = invalida["janela"]["inicio"]
    esperar(api("entregas", "POST", "/api/v1/capacidades", invalida, chave()), 400)
    for valor in ("0.00", "-1.00", "1.001", 5):
        invalida = copy.deepcopy(capacidade)
        invalida["capacidadeKg"] = valor
        esperar(api("entregas", "POST", "/api/v1/capacidades", invalida, chave()), 400)
    invalida = copy.deepcopy(capacidade)
    invalida["janela"] = {"inicio": "2020-01-01T08:00:00Z", "fim": "2020-01-01T09:00:00Z"}
    esperar(api("entregas", "POST", "/api/v1/capacidades", invalida, chave()), 400)
    esperar(api("entregas", "GET", f"/api/v1/capacidades/{chave()}"), 404)
    concorrente = copy.deepcopy(capacidade)
    concorrente["janela"] = {"inicio": (inicio + timedelta(days=1)).isoformat(),
                             "fim": (inicio + timedelta(days=1, hours=1)).isoformat()}
    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(lambda _: api("entregas", "POST", "/api/v1/capacidades", concorrente, chave()), range(2)))
    assert sorted(r["status"] for r in resultados) == [201, 409], resultados
    print("OK: capacidades persistidas, idempotência, intervalos adjacentes e concorrência sem sobreposição.")
    print("Integração concluída. Dados de demonstração mantidos nos volumes.")


if __name__ == "__main__":
    main()
