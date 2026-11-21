"""Paso de pipeline (no es agente): extracción de texto por página.

- Usa la capa de texto nativa del PDF si existe.
- Si la página trae poco texto (escaneo), la renderiza y aplica Tesseract (local, `spa`).
- Caché en disco por SHA-256 del archivo: el demo en vivo no repite OCR.
Motores: Tesseract (sin IA, local; por defecto) o visión del LLM (OCR_MOTOR=vision).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image

from .config import DIR_CACHE, cfg
from .schemas import Documento, Pagina

if os.getenv("TESSERACT_CMD"):
    pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")

EXT_PDF = {".pdf"}
EXT_IMG = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def sha256(ruta: str | Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _ocr_imagen(png: bytes, idioma: str) -> tuple[str, float]:
    img = Image.open(io.BytesIO(png))
    datos = pytesseract.image_to_data(img, lang=idioma, output_type=pytesseract.Output.DICT, config="--psm 3")
    lineas: dict[tuple, list[str]] = {}
    confs = []
    for i, palabra in enumerate(datos["text"]):
        if not palabra.strip():
            continue
        clave = (datos["block_num"][i], datos["par_num"][i], datos["line_num"][i])
        lineas.setdefault(clave, []).append(palabra)
        c = float(datos["conf"][i])
        if c >= 0:
            confs.append(c)
    texto = "\n".join(" ".join(p) for _, p in sorted(lineas.items()))
    calidad = (sum(confs) / len(confs) / 100) if confs else 0.0
    return texto, round(calidad, 3)


def _ocr_vision(png: bytes) -> tuple[str, float]:
    """OCR con el LLM multimodal (alternativa con IA a Tesseract)."""
    import base64

    from langchain_core.messages import HumanMessage

    from .config import llm

    b64 = base64.b64encode(png).decode()
    msg = HumanMessage(content=[
        {"type": "text", "text": "Transcribe TODO el texto de esta página de un documento legal mexicano, "
                                 "literalmente, respetando el orden de lectura. No resumas, no corrijas ni agregues nada. "
                                 "Marca [ilegible] donde no se lea. Devuelve solo el texto."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ])
    return llm().invoke([msg]).content, 0.9


def _ocr(png: bytes, motor: str, idioma: str) -> tuple[str, float]:
    if motor == "vision":
        from .config import soporta_vision

        try:
            if not soporta_vision():
                raise RuntimeError("el modelo local no es multimodal")
            return _ocr_vision(png)
        except Exception:  # noqa: BLE001 - si la visión falla, cae a Tesseract
            pass
    return _ocr_imagen(png, idioma)


def _limpiar(t: str) -> str:
    t = t.replace("\x00", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def extraer_texto(ruta: str | Path, doc_id: str | None = None) -> Documento:
    ruta = Path(ruta)
    h = sha256(ruta)
    ocfg = cfg()["ocr"]
    doc_id = doc_id or ruta.stem
    base = Documento(id=doc_id, nombre_archivo=ruta.name, ruta=str(ruta), sha256=h)

    DIR_CACHE.mkdir(parents=True, exist_ok=True)
    motor = os.getenv("OCR_MOTOR", "tesseract").lower()
    cache = DIR_CACHE / f"ocr_{h[:24]}_{ocfg['dpi']}_{ocfg['idioma']}{'' if motor == 'tesseract' else '_' + motor}.json"
    if cache.exists():
        paginas = [Pagina(**p) for p in json.loads(cache.read_text(encoding="utf-8"))]
        return base.model_copy(update={"paginas": paginas})

    ext = ruta.suffix.lower()
    paginas: list[Pagina] = []
    if ext in EXT_IMG:
        png = ruta.read_bytes()
        texto, cal = _ocr(png, motor, ocfg["idioma"])
        paginas = [Pagina(numero=1, texto=_limpiar(texto), fuente="ocr", calidad=cal)]
    elif ext in EXT_PDF:
        pdf = fitz.open(ruta)
        pendientes: dict[int, bytes] = {}
        nativos: dict[int, str] = {}
        for i, page in enumerate(pdf, start=1):
            t = page.get_text("text") or ""
            if len(t.strip()) >= ocfg["min_chars_texto_nativo"]:
                nativos[i] = t
            else:
                # páginas enormes: limita a ~60 Mpx para evitar el límite de Pillow y reventar la memoria
                ancho_in, alto_in = page.rect.width / 72, page.rect.height / 72
                dpi = min(ocfg["dpi"], int((60e6 / max(ancho_in * alto_in, 1)) ** 0.5))
                pendientes[i] = page.get_pixmap(dpi=max(dpi, 100)).tobytes("png")
        pdf.close()
        resultados: dict[int, tuple[str, float]] = {}
        if pendientes:
            with ThreadPoolExecutor(max_workers=ocfg.get("hilos", 4)) as ex:
                futuros = {n: ex.submit(_ocr, png, motor, ocfg["idioma"]) for n, png in pendientes.items()}
                resultados = {n: f.result() for n, f in futuros.items()}
        for n in sorted(set(nativos) | set(resultados)):
            if n in nativos:
                paginas.append(Pagina(numero=n, texto=_limpiar(nativos[n]), fuente="nativo", calidad=1.0))
            else:
                t, c = resultados[n]
                paginas.append(Pagina(numero=n, texto=_limpiar(t), fuente="ocr", calidad=c))
    else:
        return base  # formato no soportado: la Recepción lo descarta

    cache.write_text(json.dumps([p.model_dump() for p in paginas], ensure_ascii=False), encoding="utf-8")
    return base.model_copy(update={"paginas": paginas})
