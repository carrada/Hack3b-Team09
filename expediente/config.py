"""Carga de configuración (YAML), variables de entorno y fábrica del LLM."""
from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar, copy_context
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
DIR_CONFIG = RAIZ / "config"
DIR_KB = RAIZ / "kb"
DIR_CACHE = RAIZ / ".cache"

load_dotenv(RAIZ / ".env")

TIPOS = ["escrituras", "predial", "alineamiento", "uso_suelo"]
NOMBRES_TIPO = {
    "escrituras": "Escrituras",
    "predial": "Predial",
    "alineamiento": "Alineamiento y Número Oficial",
    "uso_suelo": "Uso de Suelo",
}


@lru_cache
def cfg() -> dict:
    with open(DIR_CONFIG / "dictamen.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache
def reglas(tipo: str) -> dict:
    with open(DIR_CONFIG / "reglas" / f"{tipo}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fecha_referencia() -> date:
    f = cfg().get("fecha_referencia")
    if f:
        return date.fromisoformat(str(f))
    return date.today()


_LLMS: dict = {}
_LLMS_LOCK = threading.Lock()

# Ajustes POR SESIÓN (proveedor/modelo). En la app web varios usuarios comparten el proceso: os.environ es global
# y un usuario le cambiaría el modelo a otro a media corrida. Un ContextVar vive en el hilo de cada sesión y
# LangGraph lo copia a los hilos de sus nodos; para nuestros propios pools usar `PoolConContexto`.
_AJUSTES: ContextVar[dict | None] = ContextVar("ajustes_llm", default=None)


def fijar_ajustes(proveedor: str | None = None, modelo: str | None = None) -> None:
    """Fija proveedor/modelo para el contexto actual (sesión de Streamlit). Sin llamar = valores de .env."""
    _AJUSTES.set({"proveedor": proveedor, "modelo": modelo})


class PoolConContexto(ThreadPoolExecutor):
    """ThreadPoolExecutor que hereda los ajustes de la sesión que lanza cada tarea."""

    def submit(self, fn, /, *args, **kwargs):
        return super().submit(copy_context().run, fn, *args, **kwargs)


def proveedor() -> str:
    a = _AJUSTES.get()
    return ((a or {}).get("proveedor") or os.getenv("LLM_PROVIDER", "openai")).lower()


def modelo() -> str:
    a = _AJUSTES.get() or {}
    if a.get("modelo") and (a.get("proveedor") or "").lower() == proveedor():
        return a["modelo"]
    if proveedor() == "ollama":
        return os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
    return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def modelos_ollama() -> list[str]:
    """Modelos instalados en el Ollama local (vacío si el servicio no responde)."""
    import json
    import urllib.request

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=3) as r:
            return [m["name"] for m in json.load(r).get("models", [])]
    except Exception:  # noqa: BLE001
        return []


def modelo_vision() -> str:
    """Modelo que lee los escaneos. Por defecto el mismo de los agentes (un solo modelo en GPU, sin recargas)."""
    if proveedor() == "ollama":
        return os.getenv("OLLAMA_VISION_MODEL") or modelo()
    return os.getenv("OPENAI_VISION_MODEL") or modelo()


def es_multimodal(nombre: str) -> bool:
    return any(k in nombre.lower() for k in ("llava", "vl", "vision", "gemma3", "minicpm-v", "moondream", "granite3.2-vision"))


def soporta_vision() -> bool:
    """OpenAI sí; en Ollama solo modelos multimodales (qwen2.5vl, llava, llama3.2-vision, gemma3…)."""
    return proveedor() != "ollama" or es_multimodal(modelo_vision())


def _crear(prov: str, nombre: str):
    if prov == "ollama":
        from langchain_ollama import ChatOllama

        # OLLAMA_NUM_GPU=99 fuerza todas las capas a la GPU: Ollama reserva de más para los modelos con visión
        # y deja la mitad en CPU (4x más lento en una GPU de 4 GB). Vacío = que Ollama decida.
        num_gpu = os.getenv("OLLAMA_NUM_GPU")
        return ChatOllama(
            model=nombre, temperature=0, num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),
            num_gpu=int(num_gpu) if num_gpu else None,
            keep_alive=os.getenv("OLLAMA_KEEP_ALIVE", "30m"),  # el modelo se queda en GPU entre documentos
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=nombre, temperature=0, max_retries=3, timeout=120)


def _obtener(nombre: str):
    clave = (proveedor(), nombre)
    if clave not in _LLMS:
        with _LLMS_LOCK:  # dos sesiones pueden pedir el mismo cliente a la vez
            if clave not in _LLMS:
                _LLMS[clave] = _crear(*clave)
    return _LLMS[clave]


def llm():
    """LLM de chat según LLM_PROVIDER (openai | ollama). Se cachea por proveedor+modelo, así que se puede cambiar en caliente."""
    return _obtener(modelo())


def llm_vision():
    if not soporta_vision():
        raise RuntimeError(f"el modelo «{modelo_vision()}» no es multimodal: elige uno con visión (p. ej. qwen2.5vl:3b)")
    return _obtener(modelo_vision())


def llm_estructurado(esquema):
    return llm().with_structured_output(esquema, method="json_schema")
