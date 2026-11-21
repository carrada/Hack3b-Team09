"""La API no debe inventar un dictamen si el modelo no está disponible."""
from fastapi.testclient import TestClient

from expediente.api import app

client = TestClient(app)


def test_health_sin_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    respuesta = client.get("/api/v1/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "degraded"
    assert "OPENAI_API_KEY" in cuerpo["detalle"]


def test_analisis_sin_llm_no_inventa_dictamen(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    respuesta = client.post(
        "/api/v1/analisis",
        data={"uso": "tienda"},
        files=[("files", ("boleta.pdf", b"%PDF-1.4 vacio", "application/pdf"))],
    )
    assert respuesta.status_code == 503
    assert "dictamen" not in respuesta.json()
    assert "OPENAI_API_KEY" in respuesta.json()["detail"]


def test_uso_invalido(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    respuesta = client.post(
        "/api/v1/analisis",
        data={"uso": "otro"},
        files=[("files", ("boleta.pdf", b"%PDF-1.4", "application/pdf"))],
    )
    assert respuesta.status_code == 422
    assert "tienda" in respuesta.json()["detail"]
