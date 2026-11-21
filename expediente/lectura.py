"""Paso de pipeline (no es agente): lectura del texto de cada página.

- Si la página trae capa de texto nativa (PDF digital), se usa tal cual: exacta e instantánea.
- Si es un escaneo o una imagen, la lee el LLM con visión (local con Ollama o OpenAI). No hay OCR clásico.
- Caché en disco por SHA-256 del archivo + modelo: el demo en vivo no repite lecturas.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf as fitz
from PIL import Image

from .config import DIR_CACHE, cfg, llm_vision, modelo_vision, proveedor
from .schemas import Documento, Pagina

EXT_PDF = {".pdf"}
EXT_IMG = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}

# Prompt corto y sin pedir marcas tipo "[ilegible]": los modelos chicos (3B) responden solo con la marca.
PROMPT = "Transcribe el texto de esta imagen tal como aparece, línea por línea. Devuelve solo el texto."


def sha256(ruta: str | Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _a_jpeg(img: Image.Image, lado_max: int) -> bytes:
    """Reduce la imagen: los modelos de visión cobran (en tiempo y tokens) por píxel."""
    img = img.convert("RGB")
    img.thumbnail((lado_max, lado_max))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def _leer_imagen(jpeg: bytes) -> str:
    from langchain_core.messages import HumanMessage

    b64 = base64.b64encode(jpeg).decode()
    msg = HumanMessage(content=[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                                {"type": "text", "text": PROMPT}])
    ultimo = None
    for _ in range(2):  # un reintento; si vuelve a fallar la página queda vacía y la Recepción lo reporta
        try:
            return llm_vision().invoke([msg]).content
        except Exception as e:  # noqa: BLE001
            ultimo = e
    raise RuntimeError(f"el modelo de visión no pudo leer la página: {ultimo}")


def _limpiar(t: str) -> str:
    t = t.replace("\x00", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def extraer_texto(ruta: str | Path, doc_id: str | None = None) -> Documento:
    ruta = Path(ruta)
    h = sha256(ruta)
    lcfg = cfg()["lectura"]
    doc_id = doc_id or ruta.stem
    base = Documento(id=doc_id, nombre_archivo=ruta.name, ruta=str(ruta), sha256=h)

    DIR_CACHE.mkdir(parents=True, exist_ok=True)
    etiqueta = re.sub(r"[^\w.-]+", "-", f"{proveedor()}_{modelo_vision()}_{lcfg['lado_max_px']}")
    cache = DIR_CACHE / f"lectura_{h[:24]}_{etiqueta}.json"
    if cache.exists():
        paginas = [Pagina(**p) for p in json.loads(cache.read_text(encoding="utf-8"))]
        return base.model_copy(update={"paginas": paginas})

    ext = ruta.suffix.lower()
    nativos: dict[int, str] = {}
    pendientes: dict[int, bytes] = {}
    if ext in EXT_IMG:
        pendientes[1] = _a_jpeg(Image.open(ruta), lcfg["lado_max_px"])
    elif ext in EXT_PDF:
        pdf = fitz.open(ruta)
        for i, page in enumerate(pdf, start=1):
            t = page.get_text("text") or ""
            if len(t.strip()) >= lcfg["min_chars_texto_nativo"]:
                nativos[i] = t
            else:
                # se renderiza ya al tamaño final: evita rasterizar a 300 dpi para luego reducir
                escala = lcfg["lado_max_px"] / max(page.rect.width, page.rect.height)
                pix = page.get_pixmap(matrix=fitz.Matrix(escala, escala))
                pendientes[i] = _a_jpeg(Image.frombytes("RGB", (pix.width, pix.height), pix.samples), lcfg["lado_max_px"])
        pdf.close()
    else:
        return base  # formato no soportado: la Recepción lo descarta

    leidas: dict[int, str] = {}
    fallos = 0
    if pendientes:
        with ThreadPoolExecutor(max_workers=lcfg.get("hilos", 2)) as ex:
            futuros = {n: ex.submit(_leer_imagen, img) for n, img in pendientes.items()}
            for n, f in futuros.items():
                try:
                    leidas[n] = f.result()
                except Exception:  # noqa: BLE001 - la página queda vacía; no se guarda en caché
                    leidas[n] = ""
                    fallos += 1
    paginas = [Pagina(numero=n, texto=_limpiar(nativos[n] if n in nativos else leidas[n]),
                      fuente="nativo" if n in nativos else "vision")
               for n in sorted(set(nativos) | set(leidas))]
    if not fallos:
        cache.write_text(json.dumps([p.model_dump() for p in paginas], ensure_ascii=False), encoding="utf-8")
    return base.model_copy(update={"paginas": paginas})
