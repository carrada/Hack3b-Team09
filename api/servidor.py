"""API HTTP que conecta el frontend tiendas-3b con el backend multiagente (sin cambiar ninguno de los dos por dentro).

Sirve el frontend y responde las MISMAS rutas que antes eran archivos estáticos precalculados, ahora con datos reales:
    GET  /analisis/indice.json        documentos analizados
    GET  /analisis/expedientes.json   expedientes (uno por predio) con sus documentos y el dictamen del backend
    GET  /analisis/<id>.json          análisis de un documento (contrato de tiendas-3b/modulo.js)
    GET  /paginas/<id>/p<n>.jpg       imagen de la página n del PDF
y agrega:
    POST /api/expedientes/<exp>/documentos   sube PDFs (campo `files`, opcional `tipo`, `uso`): se analizan en segundo plano
    GET  /api/expedientes/<exp>              estado del análisis (en_fila | procesando | listo | error)
    GET  /api/health

Los análisis locales pasan por la misma fila que la app de Streamlit (expediente.fila): uno a la vez en la GPU.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
import traceback
from pathlib import Path

import pymupdf as fitz
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from expediente.config import DIR_CACHE, RAIZ, proveedor
from expediente.fila import Fila

from .contrato import ANCHO_IMG, convertir

FRONTEND = RAIZ / "tiendas-3b"
DATOS = DIR_CACHE / "api"                  # .cache/ está en .gitignore: aquí viven PDFs subidos y resultados
DIR_EXP, DIR_AN, DIR_PAG = DATOS / "expedientes", DATOS / "analisis", DATOS / "paginas"
for d in (DIR_EXP, DIR_AN, DIR_PAG):
    d.mkdir(parents=True, exist_ok=True)

fila = Fila({"ollama": int(os.getenv("FILA_OLLAMA", "1")), "openai": int(os.getenv("FILA_OPENAI", "4"))})
_lock = threading.RLock()
_trabajos: dict[str, dict] = {}            # exp -> {estado, posicion, error, rehacer}


def _id_seguro(x: str) -> str:
    x = re.sub(r"[^\w\-]+", "_", x.strip())[:80]
    if not x:
        raise HTTPException(400, "Identificador de expediente vacío")
    return x


def _leer(p: Path, defecto=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return defecto


def _escribir(p: Path, obj) -> None:
    tmp = p.with_suffix(f".{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def _ficha(exp: str) -> dict:
    return _leer(DIR_EXP / exp / "ficha.json", {}) or {}


def _publico(a: dict) -> dict:
    return {k: v for k, v in a.items() if not k.startswith("_")}


# ------------------------------------------------------------------ análisis en segundo plano
def _procesar(exp: str, uso: str) -> None:
    from expediente.reporte import ejecutar  # import tardío: carga LangGraph/LLM solo al primer análisis

    while True:
        with _lock:
            _trabajos[exp].update(estado="en_fila", rehacer=False, error=None)
        turno = fila.entrar(proveedor())
        completado = False
        try:
            while not fila.esperar(turno, 1.0):  # cada vuelta es el latido del turno
                with _lock:
                    _trabajos[exp]["posicion"] = fila.posicion(turno)
            with _lock:
                _trabajos[exp].update(estado="procesando", posicion=0, inicio=time.time())
            carpeta = DIR_EXP / exp / "docs"
            archivos = sorted(str(p) for p in carpeta.iterdir() if p.is_file())
            estado, _ = ejecutar(archivos, uso)
            ficha, analisis = convertir(exp, estado)
            previa = _ficha(exp)
            for viejo in previa.get("docs", {}).values():  # análisis anteriores de este expediente
                (DIR_AN / f"{viejo}.json").unlink(missing_ok=True)
                shutil.rmtree(DIR_PAG / viejo, ignore_errors=True)
            for a in analisis:
                _escribir(DIR_AN / f"{a['id']}.json", a)
                shutil.rmtree(DIR_PAG / a["id"], ignore_errors=True)  # páginas viejas en caché
            ficha.update(uso=uso, actualizado=time.time(), duracion=round(time.time() - _trabajos[exp]["inicio"], 1),
                         bitacora=estado.get("bitacora", []))
            _escribir(DIR_EXP / exp / "ficha.json", ficha)
            completado = True
            with _lock:
                _trabajos[exp]["estado"] = "listo"
        except Exception as e:  # noqa: BLE001 - el error se reporta al frontend
            traceback.print_exc()
            with _lock:
                _trabajos[exp].update(estado="error", error=str(e))
        finally:
            fila.salir(turno, completado=completado)
        with _lock:  # si llegaron más PDFs mientras se analizaba, se vuelve a correr con todos
            if not _trabajos[exp].get("rehacer"):
                return


def _lanzar(exp: str, uso: str) -> None:
    with _lock:
        t = _trabajos.get(exp)
        if t and t["estado"] in ("en_fila", "procesando"):
            t["rehacer"] = True
            return
        _trabajos[exp] = {"estado": "en_fila", "posicion": None, "error": None, "rehacer": False}
    threading.Thread(target=_procesar, args=(exp, uso), daemon=True, name=f"analisis-{exp}").start()


# ------------------------------------------------------------------ app
app = FastAPI(title="Expedientes 3B · API", version="1.0")


@app.get("/api/health")
def health():
    return {"status": "ok", "proveedor": proveedor()}


@app.post("/api/expedientes/{exp}/documentos", status_code=202)
async def subir(exp: str, files: list[UploadFile] = File(...), tipo: str | None = Form(None),
                uso: str = Form("tienda")):
    exp = _id_seguro(exp)
    carpeta = DIR_EXP / exp / "docs"
    carpeta.mkdir(parents=True, exist_ok=True)
    if tipo:  # "Cambiar" el PDF de un tipo: se quita el anterior de ese tipo
        ficha = _ficha(exp)
        aid = ficha.get("docs", {}).get(tipo)
        a = _leer(DIR_AN / f"{aid}.json", {}) if aid else {}
        if a.get("_ruta"):
            Path(a["_ruta"]).unlink(missing_ok=True)
    recibidos, rechazados = [], []
    for f in files:
        nombre = Path(f.filename or "documento.pdf").name
        if not (nombre.lower().endswith(".pdf") or f.content_type == "application/pdf"):
            rechazados.append(f"{nombre}: no es un PDF")
            continue
        destino = carpeta / nombre
        i = 1
        while destino.exists():
            destino = carpeta / f"{Path(nombre).stem}_{i}{Path(nombre).suffix}"
            i += 1
        destino.write_bytes(await f.read())
        recibidos.append(nombre)
    if recibidos:
        _lanzar(exp, uso if uso in ("tienda", "cedis") else "tienda")
    return {"expediente": exp, "recibidos": recibidos, "rechazados": rechazados, **estado_expediente(exp)}


@app.get("/api/expedientes/{exp}")
def estado_expediente(exp: str):
    exp = _id_seguro(exp)
    with _lock:
        t = dict(_trabajos.get(exp) or {})
    ficha = _ficha(exp)
    if not t:
        t = {"estado": "listo" if ficha else "sin_documentos"}
    return {"estado": t.get("estado"), "posicion": t.get("posicion"), "error": t.get("error"),
            "docs": ficha.get("docs", {}), "archivos": {k: (_leer(DIR_AN / f"{v}.json", {}) or {}).get("archivo")
                                                         for k, v in ficha.get("docs", {}).items()},
            "dictamen": ficha.get("dictamen"), "duracion": ficha.get("duracion")}


@app.get("/analisis/expedientes.json")
def expedientes():
    fichas = [_leer(p / "ficha.json") for p in sorted(DIR_EXP.iterdir()) if (p / "ficha.json").exists()]
    return [{k: v for k, v in f.items() if k != "bitacora"} for f in fichas if f]


@app.get("/analisis/indice.json")
def indice():
    out = []
    for p in sorted(DIR_AN.glob("*.json")):
        a = _leer(p)
        if a:
            out.append({"id": a["id"], "archivo": a["archivo"], "originales": [a["archivo"]], "bytes": a.get("bytes", 0),
                        "titulo": a["titulo"], "paginas": a["total_paginas"], "pasos": len(a["pasos"]),
                        "revisar": a["resumen"]["revisar"], "tipo": a["tipo"], "grupo": a["grupo"]})
    return out


@app.get("/analisis/{aid}.json")
def analisis(aid: str):
    a = _leer(DIR_AN / f"{_id_seguro(aid)}.json")
    if not a:
        raise HTTPException(404, f"No existe el análisis {aid}")
    return JSONResponse(_publico(a))


@app.get("/paginas/{aid}/p{n}.jpg")
def pagina(aid: str, n: int):
    aid = _id_seguro(aid)
    destino = DIR_PAG / aid / f"p{n}.jpg"
    if not destino.exists():
        a = _leer(DIR_AN / f"{aid}.json")
        if not a or not a.get("_ruta") or not Path(a["_ruta"]).exists():
            raise HTTPException(404, "Página no disponible")
        with fitz.open(a["_ruta"]) as pdf:
            if not 1 <= n <= len(pdf):
                raise HTTPException(404, "Página fuera de rango")
            pg = pdf[n - 1]
            escala = ANCHO_IMG / max(pg.rect.width, 1)
            destino.parent.mkdir(parents=True, exist_ok=True)
            pg.get_pixmap(matrix=fitz.Matrix(escala, escala)).save(str(destino), jpg_quality=82)
    return FileResponse(destino, media_type="image/jpeg")


@app.get("/")
def inicio():
    return RedirectResponse("/index.html")


@app.get("/index.html")
def mapa():
    """El mapa trae el token de Mapbox como marcador; se inserta desde .env (MAPBOX_TOKEN) para no guardarlo en git."""
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    token = os.getenv("MAPBOX_TOKEN", "").strip()
    if token:
        html = html.replace("PON_AQUI_TU_TOKEN_DE_MAPBOX", token)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


# el frontend (al final: las rutas de arriba tienen prioridad sobre los archivos estáticos)
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
