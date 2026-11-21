"""Carga de configuración (YAML), variables de entorno y fábrica del LLM."""
from __future__ import annotations

import os
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


def proveedor() -> str:
    """openai | ollama | ollama_cloud."""
    return os.getenv("LLM_PROVIDER", "openai").lower().strip()


def modelo() -> str:
    prov = proveedor()
    if prov == "ollama":
        return os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    if prov == "ollama_cloud":
        return os.getenv("OLLAMA_CLOUD_MODEL", os.getenv("OLLAMA_MODEL", "gemma4:31b"))
    return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def ollama_api_key() -> str:
    return os.getenv("OLLAMA_API_KEY", "").strip()


def modelos_ollama() -> list[str]:
    """Modelos instalados en el Ollama local (vacío si el servicio no responde)."""
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(f"{ollama_host()}/api/tags", timeout=3) as r:
            return [m["name"] for m in json.load(r).get("models", [])]
    except Exception:  # noqa: BLE001
        return []


def modelo_ollama_instalado(nombre: str | None = None) -> bool:
    """True si el tag local coincide con el modelo pedido (acepta sufijo :latest)."""
    pedido = (nombre or modelo()).strip()
    if not pedido:
        return False
    instalados = modelos_ollama()
    if pedido in instalados:
        return True
    base = pedido.split(":")[0]
    return any(m == pedido or m.startswith(f"{base}:") for m in instalados)


def soporta_vision() -> bool:
    """OpenAI y ollama_cloud sí; en Ollama local solo modelos multimodales."""
    if proveedor() != "ollama":
        return True
    return any(k in modelo().lower() for k in ("llava", "vl", "vision", "gemma3", "minicpm-v", "moondream"))


def llm():
    """LLM según LLM_PROVIDER (openai | ollama | ollama_cloud). Cache por proveedor+modelo."""
    clave = (proveedor(), modelo())
    if clave not in _LLMS:
        if clave[0] == "ollama":
            from langchain_ollama import ChatOllama

            _LLMS[clave] = ChatOllama(
                model=clave[1],
                temperature=0,
                num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),
                base_url=ollama_host(),
            )
        elif clave[0] == "ollama_cloud":
            from langchain_openai import ChatOpenAI

            # Compat OpenAI hacia https://ollama.com/v1 (docs.ollama.com/api/openai-compatibility).
            _LLMS[clave] = ChatOpenAI(
                model=clave[1],
                temperature=0,
                max_retries=3,
                timeout=120,
                api_key=ollama_api_key() or "missing-ollama-api-key",
                base_url="https://ollama.com/v1",
            )
        else:
            from langchain_openai import ChatOpenAI

            _LLMS[clave] = ChatOpenAI(model=clave[1], temperature=0, max_retries=3, timeout=120)
    return _LLMS[clave]


def llm_estructurado(esquema):
    return llm().with_structured_output(esquema, method="json_schema")
