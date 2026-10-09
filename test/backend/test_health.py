"""Task 1.2 — contrato operativo: GET /api/health + forma única de error (TDD RED)."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict


def _client() -> TestClient:
    from app.main import create_app

    return TestClient(create_app())


def test_health_responde_ok_sin_auth() -> None:
    client = _client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_error_404_usa_forma_unica() -> None:
    client = _client()
    resp = client.get("/api/ruta-que-no-existe")
    assert resp.status_code == 404
    body = resp.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) >= {"code", "message"}


def _strict_app() -> TestClient:
    from app.core.errors import register_error_handlers

    class DemoIn(BaseModel):
        model_config = ConfigDict(extra="forbid")

        nombre: str

    strict = FastAPI()
    register_error_handlers(strict)

    @strict.post("/demo")
    async def _demo(payload: DemoIn) -> dict[str, str]:
        return {"nombre": payload.nombre}

    @strict.get("/boom")
    async def _boom() -> dict[str, str]:
        raise RuntimeError("postgresql://SECRETO-que-no-debe-filtrarse")

    return TestClient(strict, raise_server_exceptions=False)


def test_payload_con_campo_desconocido_responde_422_forma_unica() -> None:
    client = _strict_app()
    resp = client.post("/demo", json={"nombre": "Ana", "campoFantasma": 1})
    assert resp.status_code == 422
    body = resp.json()
    assert set(body.keys()) == {"error"}
    assert body["error"]["code"] == "unprocessable_entity"


def test_error_interno_500_sin_detalles_internos() -> None:
    client = _strict_app()
    resp = client.get("/boom")
    assert resp.status_code == 500
    raw = resp.text
    assert "SECRETO-que-no-debe-filtrarse" not in raw
    assert "Traceback" not in raw
    assert set(resp.json().keys()) == {"error"}
