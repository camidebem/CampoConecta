"""Emite e valida JWT de desenvolvimento para a borda local."""

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel


app = FastAPI(title="CampoConecta - authn-verify", version="1.0.0")

JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_EXPIRES_MINUTES = int(os.environ.get("JWT_EXPIRES_MINUTES", "60"))


class Emissao(BaseModel):
    sub: str
    papel: str
    instituicaoId: str | None = None
    produtorId: str | None = None


def claims_validas(claims: dict) -> bool:
    papel = claims.get("papel")
    if not claims.get("sub") or papel not in {"gestor", "escola", "produtor"}:
        return False
    if papel in {"gestor", "escola"}:
        return bool(claims.get("instituicaoId"))
    return bool(claims.get("produtorId"))


def criar_token(dados: Emissao) -> str:
    agora = datetime.now(timezone.utc)
    claims = dados.model_dump(exclude_none=True)
    if not claims_validas(claims):
        raise HTTPException(status_code=400, detail="Claims de identidade invalidas.")
    claims.update({
        "iss": "campoconecta-dev",
        "aud": "campoconecta",
        "iat": agora,
        "exp": agora + timedelta(minutes=JWT_EXPIRES_MINUTES),
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(claims, JWT_SECRET, algorithm="HS256")


@app.get("/health")
def health():
    return {"status": "ok" if JWT_SECRET else "indisponivel", "servico": "authn-verify"}


@app.post("/token")
def emitir(dados: Emissao):
    if not JWT_SECRET:
        raise HTTPException(status_code=503, detail="JWT_SECRET nao configurado.")
    return {"token": criar_token(dados), "tokenType": "Bearer"}


@app.get("/verify")
def verificar(request: Request, authorization: str | None = Header(default=None)):
    if not JWT_SECRET:
        raise HTTPException(status_code=503, detail="JWT_SECRET nao configurado.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization Bearer ausente.")

    try:
        claims = jwt.decode(
            authorization.removeprefix("Bearer ").strip(),
            JWT_SECRET,
            algorithms=["HS256"],
            audience="campoconecta",
            issuer="campoconecta-dev",
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="JWT invalido.")

    if not claims_validas(claims):
        raise HTTPException(status_code=403, detail="Papel ou vinculo invalido.")

    uri = request.headers.get("x-original-uri", "")
    if uri.startswith("/prefeitura/") and claims["papel"] not in {"gestor", "escola"}:
        raise HTTPException(status_code=403, detail="Papel incompatível com o portal.")
    if uri.startswith("/produtor/") and claims["papel"] != "produtor":
        raise HTTPException(status_code=403, detail="Papel incompatível com o aplicativo.")

    headers = {
        "X-Authenticated-Subject": str(claims["sub"]),
        "X-Authenticated-Role": str(claims["papel"]),
        "X-Authenticated-Institution": str(claims.get("instituicaoId", "")),
        "X-Authenticated-Producer": str(claims.get("produtorId", "")),
    }
    return Response(status_code=204, headers=headers)