"""Carga una carpeta de expedientes (una subcarpeta = un expediente/zona) en el backend vía la API.

    python -m api.importar Expedientes [--proveedor openai|ollama] [--servidor http://127.0.0.1:8000]

Cada subcarpeta se sube con sus PDFs (los demás archivos se ignoran) y el backend la analiza en segundo plano con la
misma fila que el resto. Los expedientes chicos van primero para que el mapa se llene rápido. Requiere `python -m api`
corriendo.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import httpx
import pymupdf as fitz


def paginas(carpeta: Path) -> int:
    total = 0
    for p in carpeta.glob("*.pdf"):
        try:
            with fitz.open(p) as d:
                total += len(d)
        except Exception:  # noqa: BLE001
            pass
    return total


def main(argv=None) -> int:
    a = argparse.ArgumentParser(prog="python -m api.importar")
    a.add_argument("carpeta")
    a.add_argument("--proveedor", choices=["openai", "ollama"])
    a.add_argument("--servidor", default="http://127.0.0.1:8000")
    args = a.parse_args(argv)

    raiz = Path(args.carpeta)
    carpetas = sorted((d for d in raiz.iterdir() if d.is_dir() and any(d.glob("*.pdf"))), key=paginas)
    cli = httpx.Client(base_url=args.servidor, timeout=120)
    for d in carpetas:
        pdfs = sorted(d.glob("*.pdf"))
        files = [("files", (p.name, p.read_bytes(), "application/pdf")) for p in pdfs]
        data = {"proveedor": args.proveedor} if args.proveedor else {}
        r = cli.post(f"/api/expedientes/{d.name}/documentos", files=files, data=data)
        r.raise_for_status()
        print(f"↑ {d.name}: {len(pdfs)} PDF, {paginas(d)} págs → {r.json()['estado']}", flush=True)

    pendientes, t0 = {d.name for d in carpetas}, time.time()
    while pendientes:
        time.sleep(5)
        for exp in sorted(pendientes):
            e = cli.get(f"/api/expedientes/{exp}").json()
            if e["estado"] in ("listo", "error"):
                pendientes.discard(exp)
                dic = e.get("dictamen") or {}
                detalle = (f"{dic.get('recomendacion')} · confianza {dic.get('confianza')} · docs {sorted(e['docs'])}"
                           if e["estado"] == "listo" else e.get("error"))
                print(f"{'✓' if e['estado'] == 'listo' else '✗'} {exp} ({time.time() - t0:.0f}s) {detalle}", flush=True)
    print(f"Listo: {len(carpetas)} expedientes en {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
