"""Ejecución del grafo y reporte en Markdown."""
from __future__ import annotations

import uuid

from .config import NOMBRES_TIPO, cfg
from .schemas import ETIQUETA, ICONO, Cruce, Dictamen, ResultadoDocumento


def ejecutar(archivos: list[str], uso: str = "tienda", hitl: bool = False, grafo=None, thread_id: str | None = None):
    from .graph import construir_grafo

    grafo = grafo or construir_grafo()
    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
    estado = grafo.invoke({"archivos": archivos, "uso_requerido": uso, "hitl": hitl, "resultados": [], "bitacora": []}, config)
    return estado, config


def _cita(ev: dict | None) -> str:
    if not ev:
        return "—"
    marca = "✔" if ev.get("verificada") else "✖ no verificada"
    frag = ev["fragmento"].replace("\n", " ").replace("|", "/")[:140]
    return f"{ev['documento_id']} p.{ev['pagina']}: «{frag}» ({marca})"


def markdown(estado: dict) -> str:
    d = Dictamen.model_validate(estado["dictamen"])
    resultados = [ResultadoDocumento.model_validate(r) for r in estado.get("resultados_verificados") or estado.get("resultados", [])]
    cruces = [Cruce.model_validate(c) for c in estado.get("cruces", [])]
    uso = cfg()["usos_requeridos"].get(d.uso_requerido, {}).get("etiqueta", d.uso_requerido)
    L = [f"# Dictamen de expediente · {ICONO[d.recomendacion]} {ETIQUETA[d.recomendacion]}",
         "", f"**Uso requerido:** {uso} · **Confianza:** {d.confianza}/100 · "
         f"**Citas verificadas:** {d.citas_verificadas}/{d.citas_total} · "
         f"**Revisión humana:** {'Sí' if d.requiere_humano else 'No'}", "", d.resumen or "", "",
         "## Razones", *[f"- {r}" for r in d.razones], "",
         "## Documentos", "**Recibidos:**", *[f"- {x}" for x in d.documentos_recibidos],
         "", f"**Faltantes:** {', '.join(d.documentos_faltantes) or 'ninguno'}"]
    if d.documentos_descartados:
        L += ["", "**Descartados:**", *[f"- {x}" for x in d.documentos_descartados]]
    L += ["", "## Señales de confianza", "| Señal | Valor |", "|---|---|",
          *[f"| {k.replace('_', ' ')} | {v:.0%} |" for k, v in d.senales_confianza.items()]]

    L += ["", "## Datos extraídos y validaciones por documento"]
    for r in resultados:
        L += ["", f"### {ICONO[r.estado]} {NOMBRES_TIPO[r.tipo]} — {r.nombre_archivo}",
              f"_Agente: {r.agente} · OCR {r.calidad_ocr:.0%} · obligatorios {r.obligatorios_encontrados}/{r.obligatorios_total}_",
              "", "| Campo | Valor | Evidencia |", "|---|---|---|"]
        for c in r.campos:
            if c.valor:
                L.append(f"| {c.nombre} | {c.valor.replace('|', '/')} | {_cita(c.evidencia.model_dump() if c.evidencia else None)} |")
        L += ["", "**Reglas evaluadas:**"]
        for h in r.hallazgos:
            icon = {"cumple": "✔", "requiere_revision": "⚠", "no_cumple": "✖"}[h.resultado] if h.severidad != "info" else "ℹ"
            L.append(f"- {icon} `{h.regla_id}` ({h.severidad}) {h.descripcion}")
            for ev in h.evidencias:
                L.append(f"    - {_cita(ev.model_dump())}")

    L += ["", "## Validaciones cruzadas", "| Atributo | Valores | Score | Resultado | Método |", "|---|---|---|---|---|"]
    for c in cruces:
        vals = "<br>".join(f"{k}: {v}" for k, v in c.valores.items()).replace("|", "/")
        L.append(f"| {c.atributo} | {vals} | {c.score:.0f} | {c.resultado} | {c.metodo} |")
    if d.discrepancias:
        L += ["", "## Inconsistencias detectadas"]
        for x in d.discrepancias:
            L += [f"- **{x.atributo}** ({x.severidad}): {x.explicacion}",
                  *[f"    - {k}: «{v}»" for k, v in x.valores.items()],
                  *[f"    - evidencia {_cita(e.model_dump())}" for e in x.evidencias]]

    L += ["", "## Requisitos cumplidos", *[f"- ✔ {x}" for x in d.requisitos_cumplidos],
          "", "## Requisitos no cumplidos / en revisión", *([f"- ✖ {x}" for x in d.requisitos_no_cumplidos] or ["- ninguno"]),
          "", "## Puntos a verificar por el equipo legal", *([f"- [ ] {x}" for x in d.puntos_a_verificar] or ["- ninguno"])]
    if estado.get("revision_humana"):
        L += ["", "## Revisión humana", f"{estado['revision_humana']}"]
    return "\n".join(L)
