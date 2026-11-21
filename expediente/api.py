"""API HTTP delgada sobre el grafo LangGraph.

No clasifica, no extrae y no dictamina por su cuenta: guarda los archivos y llama
`ejecutar()` igual que la CLI (`hitl=False`). Si el modelo no está disponible,
responde error y no inventa un dictamen.
"""
from __future__ import annotations

import os
import tempfile
import urllib.request
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import proveedor
from .reporte import ejecutar

USOS = {"tienda", "cedis"}

app = FastAPI(title="Expedientes 3B", version="backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def llm_disponible() -> tuple[bool, str]:
    """True solo si el proveedor configurado puede atender. No llama al grafo."""
    if proveedor() == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        try:
            with urllib.request.urlopen(f"{host}/api/tags", timeout=3) as resp:
                if resp.status >= 400:
                    return False, f"Ollama respondió {resp.status} en {host}."
        except Exception as exc:  # noqa: BLE001 - el fallo de red es la respuesta
            return False, f"Ollama no responde en {host}: {exc}"
        return True, ""

    clave = os.getenv("OPENAI_API_KEY", "").strip()
    if not clave:
        return False, (
            "OPENAI_API_KEY no está configurada. Copia .env.example a .env y coloca la clave, "
            "o arranca con LLM_PROVIDER=ollama."
        )
    return True, ""


def estado_publico(estado: dict) -> dict:
    dictamen = estado.get("dictamen")
    if not dictamen:
        raise HTTPException(
            status_code=500,
            detail="El grafo terminó sin dictamen. No se inventa un resultado.",
        )
    return {
        "dictamen": dictamen,
        "bitacora": list(estado.get("bitacora") or []),
        "resultados_verificados": list(
            estado.get("resultados_verificados") or estado.get("resultados") or []
        ),
        "cruces": list(estado.get("cruces") or []),
        "discrepancias": list(estado.get("discrepancias") or []),
    }


@app.get("/api/v1/health")
def health() -> dict:
    ok, motivo = llm_disponible()
    cuerpo = {"status": "ok" if ok else "degraded", "version": "backend"}
    if motivo:
        cuerpo["detalle"] = motivo
    return cuerpo


@app.post("/api/v1/analisis")
async def analisis(
    uso: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    if uso not in USOS:
        raise HTTPException(status_code=422, detail="uso debe ser tienda o cedis.")
    if not files:
        raise HTTPException(status_code=400, detail="Sube al menos un archivo.")

    ok, motivo = llm_disponible()
    if not ok:
        raise HTTPException(status_code=503, detail=motivo)

    with tempfile.TemporaryDirectory(prefix="expediente-") as tmp:
        rutas: list[str] = []
        for indice, upload in enumerate(files):
            nombre = Path(upload.filename or f"documento-{indice}").name
            if nombre in {"", ".", ".."}:
                nombre = f"documento-{indice}"
            # Carpeta por archivo para conservar el nombre original (el visor lo cruza con la carga).
            destino = Path(tmp) / f"{indice:02d}" / nombre
            destino.parent.mkdir(parents=True, exist_ok=True)
            data = await upload.read()
            if not data:
                raise HTTPException(status_code=400, detail=f"El archivo {nombre} está vacío.")
            destino.write_bytes(data)
            rutas.append(str(destino))
        try:
            estado, _config = ejecutar(rutas, uso, hitl=False)
        except Exception as exc:  # noqa: BLE001 - se reporta el fallo real del grafo
            raise HTTPException(
                status_code=500,
                detail=f"El grafo no pudo terminar: {exc}",
            ) from exc

    return estado_publico(estado)
