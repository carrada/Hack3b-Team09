"""CLI.

  python -m expediente.cli analizar <carpeta|archivos...> --uso tienda|cedis
  python -m expediente.cli agrupar <carpeta_con_todos_los_pdfs> [--uso tienda] [--analizar]
  python -m expediente.cli diagrama
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .config import NOMBRES_TIPO, RAIZ

SALIDA = RAIZ / "salida"


def _archivos(rutas: list[str]) -> list[str]:
    out = []
    for r in rutas:
        p = Path(r)
        out += [str(x) for x in sorted(p.rglob("*")) if x.is_file()] if p.is_dir() else [str(p)]
    return out


def cmd_analizar(args):
    from .reporte import ejecutar, markdown

    archivos = _archivos(args.rutas)
    estado, _ = ejecutar(archivos, args.uso)
    for linea in estado.get("bitacora", []):
        print(linea)
    nombre = args.nombre or Path(args.rutas[0]).stem
    SALIDA.mkdir(exist_ok=True)
    md = markdown(estado)
    (SALIDA / f"{nombre}.md").write_text(md, encoding="utf-8")
    (SALIDA / f"{nombre}.json").write_text(json.dumps(estado, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    d = estado["dictamen"]
    print(f"\n==> {d['recomendacion'].upper()} · confianza {d['confianza']} · reporte: salida/{nombre}.md")


def cmd_agrupar(args):
    """Los datos del reto vienen agrupados por TIPO: aquí se reagrupan por INMUEBLE."""
    from .agents.recepcion import preparar_documentos

    bit: list[str] = []
    docs, descartados = preparar_documentos(_archivos(args.rutas), bit)
    grupos: dict[int, list] = {}
    for d in docs:
        grupos.setdefault(d.grupo, []).append(d)
    SALIDA.mkdir(exist_ok=True)
    resumen = []
    for g, ds in sorted(grupos.items()):
        tipos = sorted({d.tipo for d in ds})
        print(f"\nInmueble {g}: {len(ds)} docs · faltan: {[NOMBRES_TIPO[t] for t in NOMBRES_TIPO if t not in tipos]}")
        for d in ds:
            print(f"   {NOMBRES_TIPO[d.tipo]:<30} {d.nombre_archivo:<40} {d.huella.get('direccion') or ''}")
        resumen.append({"grupo": g, "archivos": [d.ruta for d in ds], "tipos": tipos,
                        "huellas": [d.huella for d in ds]})
    for d in descartados:
        print(f"Descartado: {d.nombre_archivo} — {d.motivo_descarte}")
    (SALIDA / "agrupacion.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nAgrupación guardada en salida/agrupacion.json (revísala/ajústala antes de analizar)")
    if args.analizar:
        from .reporte import ejecutar, markdown

        for g in resumen:
            estado, _ = ejecutar(g["archivos"], args.uso)
            (SALIDA / f"inmueble_{g['grupo']:02d}.md").write_text(markdown(estado), encoding="utf-8")
            print(f"Inmueble {g['grupo']}: {estado['dictamen']['recomendacion']} ({estado['dictamen']['confianza']})")


def cmd_diagrama(_):
    from .graph import construir_grafo

    g = construir_grafo().get_graph()
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "grafo.mmd").write_text(g.draw_mermaid(), encoding="utf-8")
    print(g.draw_mermaid())
    try:
        (SALIDA / "grafo.png").write_bytes(g.draw_mermaid_png())
        print("PNG: salida/grafo.png")
    except Exception as e:  # noqa: BLE001 - requiere red (mermaid.ink)
        print(f"(PNG no generado: {e})")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="expediente")
    sub = p.add_subparsers(required=True)
    a = sub.add_parser("analizar")
    a.add_argument("rutas", nargs="+")
    a.add_argument("--uso", choices=["tienda", "cedis"], default="tienda")
    a.add_argument("--nombre")
    a.add_argument("--ocr", choices=["tesseract", "vision"], help="tesseract (sin IA, local) | vision (IA, envía imágenes al LLM)")
    a.add_argument("--llm", choices=["openai", "ollama"], help="openai (nube) | ollama (modelo local)")
    a.add_argument("--modelo", help="modelo del proveedor elegido (ej. mistral:latest, gpt-4.1-mini)")
    a.set_defaults(f=cmd_analizar)
    b = sub.add_parser("agrupar")
    b.add_argument("rutas", nargs="+")
    b.add_argument("--uso", choices=["tienda", "cedis"], default="tienda")
    b.add_argument("--analizar", action="store_true")
    b.add_argument("--ocr", choices=["tesseract", "vision"], help="tesseract (sin IA, local) | vision (IA, envía imágenes al LLM)")
    b.add_argument("--llm", choices=["openai", "ollama"], help="openai (nube) | ollama (modelo local)")
    b.add_argument("--modelo", help="modelo del proveedor elegido (ej. mistral:latest, gpt-4.1-mini)")
    b.set_defaults(f=cmd_agrupar)
    c = sub.add_parser("diagrama")
    c.set_defaults(f=cmd_diagrama)
    args = p.parse_args(argv)
    if getattr(args, "llm", None):
        os.environ["LLM_PROVIDER"] = args.llm
    if getattr(args, "modelo", None):
        os.environ["OLLAMA_MODEL" if os.getenv("LLM_PROVIDER") == "ollama" else "OPENAI_MODEL"] = args.modelo
    if getattr(args, "ocr", None):
        os.environ["OCR_MOTOR"] = args.ocr
    if os.getenv("OCR_MOTOR", "tesseract") == "vision" and args.f is not cmd_diagrama:
        print("⚠️ OCR con IA: las imágenes de las páginas se envían al proveedor del LLM; más lento y con costo.")
    args.f(args)


if __name__ == "__main__":
    main()
