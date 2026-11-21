"""[1'] Dictamen: la Recepción vuelve como validador final.

1. Verifica que cada fragmento citado por los agentes exista en el texto OCR (anti-alucinación).
2. Calcula la confianza con señales medibles (no autorreportada por el LLM).
3. Aplica las reglas de dictamen: las críticas mandan; el umbral solo decide casos grises.
4. Human in the loop (interrupt) cuando la recomendación no es "Cumple".
"""
from __future__ import annotations

import json

from langgraph.types import interrupt

from ..config import NOMBRES_TIPO, cfg, llm
from ..schemas import (ETIQUETA, Cruce, Dictamen, Discrepancia, Documento, Evidencia, ExpedienteState,
                       ResultadoDocumento)
from ..tools import verificar_cita


def _verificar(ev: Evidencia, docs: dict[str, Documento], minimo: float) -> Evidencia:
    doc = docs.get(ev.documento_id)
    if not doc or not ev.fragmento:
        return ev.model_copy(update={"verificada": False, "score_verificacion": 0.0})
    paginas = {p.numero: p.texto for p in doc.paginas}
    s = verificar_cita.invoke({"texto_pagina": paginas.get(ev.pagina, ""), "fragmento": ev.fragmento})
    pagina = ev.pagina
    if s < minimo:  # quizá el agente se equivocó de página: busca en todas
        for n, t in paginas.items():
            s2 = verificar_cita.invoke({"texto_pagina": t, "fragmento": ev.fragmento})
            if s2 > s:
                s, pagina = s2, n
    return ev.model_copy(update={"verificada": s >= minimo, "score_verificacion": round(s, 1), "pagina": pagina})


def construir_dictamen(state: ExpedienteState, bitacora: list[str]) -> tuple[Dictamen, list[ResultadoDocumento], list[Discrepancia]]:
    c = cfg()
    minimo = c["verificacion_citas"]["score_minimo"]
    docs = {d["id"]: Documento.model_validate(d) for d in state.get("documentos", [])}
    resultados = [ResultadoDocumento.model_validate(r) for r in state.get("resultados", [])]
    discrepancias = [Discrepancia.model_validate(d) for d in state.get("discrepancias", [])]
    cruces = [Cruce.model_validate(x) for x in state.get("cruces", [])]
    uso = state.get("uso_requerido", "tienda")

    # ---------- 1. verificación de citas
    total = verif = 0
    for r in resultados:
        for campo in r.campos:
            if campo.evidencia:
                campo.evidencia = _verificar(campo.evidencia, docs, minimo)
                total += 1
                verif += campo.evidencia.verificada
                if not campo.evidencia.verificada:
                    campo.confianza = round(campo.confianza * 0.5, 3)
        for h in r.hallazgos:
            h.evidencias = [_verificar(e, docs, minimo) for e in h.evidencias]
    for d in discrepancias:
        d.evidencias = [_verificar(e, docs, minimo) for e in d.evidencias]
    bitacora.append(f"🔐 Dictamen: {verif}/{total} citas verificadas literalmente en el OCR")

    # ---------- 2. confianza calculada
    def prom(xs, defecto):
        xs = list(xs)
        return sum(xs) / len(xs) if xs else defecto

    req = c["documentos_requeridos"]
    senales = {
        "calidad_ocr": prom((d.calidad for d in docs.values()), 0.0),
        "campos_obligatorios": (sum(r.obligatorios_encontrados for r in resultados) /
                                max(1, sum(r.obligatorios_total for r in resultados))),
        "reglas_pasan": sum(r.reglas_pasan for r in resultados) / max(1, sum(r.reglas_evaluadas for r in resultados)),
        "cruces": prom((x.score / 100 if x.resultado == "coincide" else 0.0 for x in cruces), 0.5),
        "citas_verificadas": verif / total if total else 0.0,
    }
    confianza = round(100 * sum(c["pesos_confianza"][k] * v for k, v in senales.items()))
    tipos_presentes = {r.tipo for r in resultados}
    faltantes = [NOMBRES_TIPO[t] for t in req if t not in tipos_presentes]
    if faltantes:  # con faltantes la confianza no puede superar el umbral
        confianza = min(confianza, c["umbral_confianza"] - 1)

    # ---------- 3. reglas de dictamen
    nombre = {r.documento_id: f"{NOMBRES_TIPO[r.tipo]} ({r.nombre_archivo})" for r in resultados}
    cumplidos, no_cumplidos, razones, puntos = [], [], [], []
    criticos_no_cumple, revision = [], []

    for r in resultados:
        for h in r.hallazgos:
            if h.severidad == "info":
                continue
            etiqueta = f"[{h.regla_id}] {h.descripcion} — {nombre[r.documento_id]}"
            if h.resultado == "cumple":
                cumplidos.append(etiqueta)
                if h.severidad == "critica" and h.evidencias and not any(e.verificada for e in h.evidencias):
                    revision.append(f"La evidencia de un requisito crítico no se encontró literal en el OCR: {etiqueta}")
                    puntos.append(f"Confirmar en el original: {etiqueta}")
            else:
                no_cumplidos.append(etiqueta)
                if h.resultado == "no_cumple":
                    if h.evidencias and not any(e.verificada for e in h.evidencias):
                        revision.append(f"Posible incumplimiento con evidencia NO verificada (no se rechaza): {etiqueta}")
                        puntos.append(f"Verificar en el original: {etiqueta}")
                    else:
                        criticos_no_cumple.append(etiqueta)
                else:
                    revision.append(etiqueta)
                    puntos.append(etiqueta)

    for d in discrepancias:
        txt = f"Discrepancia de {d.atributo.replace('_', ' ')}: {d.explicacion} · " + \
              " | ".join(f"{nombre.get(k, k)}: «{v}»" for k, v in d.valores.items())
        if d.severidad == "critica":
            criticos_no_cumple.append(txt)
        else:
            revision.append(txt)
            puntos.append(txt)

    for f in faltantes:
        revision.append(f"Falta el documento: {f}")
        puntos.append(f"Solicitar {f}")
    for r in resultados:
        if r.error:
            revision.append(f"{nombre[r.documento_id]}: no se pudo analizar automáticamente")

    umbral = c["umbral_confianza"]
    if criticos_no_cumple:
        rec = "no_cumple"
        razones += [f"❌ {x}" for x in criticos_no_cumple]
    elif revision or confianza < umbral:
        rec = "requiere_revision"
    else:
        rec = "cumple"
    razones += [f"⚠️ {x}" for x in revision]
    if confianza < umbral:
        razones.append(f"⚠️ Confianza {confianza} < umbral {umbral}")
    if rec == "cumple":
        razones.append(f"✅ Los {len(req)} documentos presentes, reglas críticas cumplidas, cruces consistentes, confianza {confianza}")

    dic = Dictamen(
        recomendacion=rec, confianza=confianza, senales_confianza={k: round(v, 3) for k, v in senales.items()},
        uso_requerido=uso,
        documentos_recibidos=[f"{NOMBRES_TIPO[d.tipo]}: {d.nombre_archivo}" for d in docs.values()],
        documentos_faltantes=faltantes,
        documentos_descartados=[f"{d['nombre_archivo']}: {d['motivo_descarte']}" for d in state.get("descartados", [])],
        requisitos_cumplidos=cumplidos, requisitos_no_cumplidos=no_cumplidos, discrepancias=discrepancias,
        razones=razones, requiere_humano=rec != "cumple", puntos_a_verificar=list(dict.fromkeys(puntos)),
        citas_total=total, citas_verificadas=verif)
    return dic, resultados, discrepancias


def resumen_ejecutivo(dic: Dictamen) -> str:
    """El LLM solo redacta; los hechos vienen del dictamen calculado."""
    hechos = dic.model_dump(include={"recomendacion", "confianza", "documentos_faltantes", "razones", "uso_requerido"})
    try:
        return llm().invoke(
            "Redacta en español, para el equipo legal, un resumen de 3 a 4 oraciones del siguiente dictamen. "
            "No agregues hechos que no estén aquí. Empieza con la recomendación.\n" + json.dumps(hechos, ensure_ascii=False)
        ).content
    except Exception:  # noqa: BLE001
        return f"Recomendación: {ETIQUETA[dic.recomendacion]} (confianza {dic.confianza})."


def nodo_dictamen(state: ExpedienteState) -> dict:
    bitacora = ["━━ [1] Dictamen: verificación de citas, confianza y recomendación"]
    dic, resultados, _ = construir_dictamen(state, bitacora)
    dic.resumen = resumen_ejecutivo(dic)
    bitacora.append(f"🏁 Dictamen: {ETIQUETA[dic.recomendacion]} · confianza {dic.confianza}"
                    f"{' · se envía a revisión humana' if dic.requiere_humano else ''}")
    # reemplaza resultados por la versión con evidencias verificadas (el reducer suma, así que se marca aparte)
    return {"dictamen": dic.model_dump(), "bitacora": bitacora,
            "discrepancias": [d.model_dump() for d in dic.discrepancias],
            "resultados_verificados": [r.model_dump() for r in resultados]}


def nodo_revision_humana(state: ExpedienteState) -> dict:
    """Human in the loop: pausa el grafo con la evidencia lado a lado hasta que una persona decida."""
    dic = state["dictamen"]
    decision = interrupt({
        "mensaje": f"Recomendación automática: {ETIQUETA[dic['recomendacion']]} (confianza {dic['confianza']}). "
                   "Revise los puntos y confirme o corrija.",
        "puntos_a_verificar": dic["puntos_a_verificar"],
        "discrepancias": dic["discrepancias"],
    })
    return {"revision_humana": decision if isinstance(decision, dict) else {"decision": str(decision)},
            "bitacora": [f"👤 Revisión humana: {decision}"]}
