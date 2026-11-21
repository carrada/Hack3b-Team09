"""Motor de reglas: evalúa las reglas del YAML de cada tipo sobre los campos extraídos.

Tipos de regla soportados (ver config/reglas/*.yaml):
  campo_presente · curp_rfc · vigencia · uso_compatible · anio_pagado · autoridad_kb · llm_check
"""
from __future__ import annotations

import re

from .config import cfg, fecha_referencia, llm_estructurado
from .schemas import Campo, Documento, Evidencia, Hallazgo, JuicioLLM
from .tools import buscar_kb, corregir_ocr_id, identificadores_en, norm, usar


def _ev(campo: Campo | None) -> list[Evidencia]:
    return [campo.evidencia] if campo and campo.evidencia else []


def _h(regla: dict, doc_id: str, resultado: str, desc: str, evs: list[Evidencia], severidad: str | None = None) -> Hallazgo:
    return Hallazgo(regla_id=regla["id"], documento_id=doc_id, severidad=severidad or regla.get("severidad", "menor"),
                    resultado=resultado, descripcion=desc, evidencias=evs)


def _juicio_llm(pregunta: str, campos: dict[str, Campo], doc: Documento, bitacora: list[str]) -> JuicioLLM | None:
    contexto = "\n".join(f"- {k}: {c.valor}" for k, c in campos.items() if c.valor)
    prompt = (
        "Eres un analista legal que revisa documentos inmobiliarios en México. Responde SOLO con base en el texto.\n"
        f"Pregunta: {pregunta}\n\nCampos ya extraídos:\n{contexto}\n\n"
        "Devuelve resultado (cumple / requiere_revision / no_cumple), una explicación breve en español y una cita "
        "LITERAL corta del texto con su número de página. Si no hay información suficiente, responde requiere_revision.\n\n"
        f"TEXTO DEL DOCUMENTO:\n{doc.texto_con_paginas(30000)}"
    )
    try:
        r = llm_estructurado(JuicioLLM).invoke(prompt)
        bitacora.append(f"🧠 LLM juicio [{doc.id}]: {pregunta[:60]}… → {r.resultado}")
        return r
    except Exception as e:  # noqa: BLE001
        bitacora.append(f"⚠️ LLM juicio falló [{doc.id}]: {e}")
        return None


def evaluar(tipo_cfg: dict, campos: dict[str, Campo], doc: Documento, uso: str, bitacora: list[str]) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    hoy = fecha_referencia().isoformat()
    usos = cfg()["usos_requeridos"]
    uso_etq = usos.get(uso, {}).get("etiqueta", uso)

    for regla in tipo_cfg.get("reglas", []):
        t = regla["tipo"]
        c = campos.get(regla.get("campo", ""))
        falla = regla.get("si_falla", "requiere_revision")

        if t == "campo_presente":
            if c and c.valor:
                hallazgos.append(_h(regla, doc.id, "cumple", f"{regla['descripcion']}: «{c.valor}»", _ev(c)))
            else:
                hallazgos.append(_h(regla, doc.id, falla, f"{regla['descripcion']}: no se localizó en el documento", []))

        elif t == "curp_rfc":
            valores = []
            if c and c.valor:
                valores = identificadores_en(c.valor) or [("RFC" if len(re.sub(r'\W', '', c.valor)) <= 13 else "CURP",
                                                           re.sub(r"\W", "", c.valor.upper()))]
            if not valores:
                hallazgos.append(_h(regla, doc.id, "cumple", "No aparece CURP/RFC del titular (no aplica)", [], "info"))
                continue
            for tipo_id, val in valores:
                r = usar("validar_curp" if tipo_id == "CURP" else "validar_rfc", bitacora,
                         **({"curp": val} if tipo_id == "CURP" else {"rfc": val}))
                corregido = None if r["valida"] else corregir_ocr_id(val)
                if r["valida"]:
                    hallazgos.append(_h(regla, doc.id, "cumple", f"{tipo_id} {val}: {r['motivo']}", _ev(c)))
                elif corregido:
                    bitacora.append(f"🔧 corregir_ocr_id({val!r}) → {corregido}")
                    hallazgos.append(_h(regla, doc.id, "cumple",
                                        f"{tipo_id} leído por OCR como {val}; corrigiendo confusiones de caracteres "
                                        f"(O↔0, I↔1…) queda {corregido}, que es válido. Confirmar visualmente", _ev(c)))
                else:
                    hallazgos.append(_h(regla, doc.id, falla, f"{tipo_id} {val}: {r['motivo']}. Verificar contra el original", _ev(c)))

        elif t == "vigencia":
            ce, cv = campos.get(regla["campo_emision"]), campos.get(regla["campo_vigencia"])
            r = usar("calcular_vigencia", bitacora, fecha_emision=ce.valor if ce else None,
                     vigencia=cv.valor if cv else None, fecha_ref=hoy,
                     dias_alerta=regla.get("dias_alerta", 30), vigencia_default_dias=regla.get("vigencia_default_dias"))
            evs = _ev(ce) + _ev(cv)
            est = r["estado"]
            if est in ("vigente", "sin_vencimiento"):
                txt = "sin vencimiento" if est == "sin_vencimiento" else f"vence {r['vence']} ({r['dias_restantes']} días)"
                hallazgos.append(_h(regla, doc.id, "cumple", f"{regla['descripcion']}: {txt}", evs))
            elif est == "por_vencer":
                hallazgos.append(_h(regla, doc.id, "requiere_revision", f"Vigencia por vencer: vence {r['vence']} ({r['dias_restantes']} días)", evs))
            elif est == "vencido":
                hallazgos.append(_h(regla, doc.id, regla.get("si_vencido", "requiere_revision"),
                                    f"Documento vencido: venció {r['vence']} (emitido {r['emision']})", evs))
            else:
                res = regla.get("si_indeterminable", "requiere_revision")
                sev = "info" if res == "info" else regla.get("severidad", "menor")
                hallazgos.append(_h(regla, doc.id, "cumple" if res == "info" else res,
                                    "Vigencia no determinable con la información del documento", evs, sev))

        elif t == "uso_compatible":
            u = usos.get(uso, {})
            valor = " ".join(x.valor for x in [c, campos.get("zonificacion")] if x and x.valor)
            if not valor:
                hallazgos.append(_h(regla, doc.id, "requiere_revision", f"No se localizó el uso autorizado para evaluar compatibilidad con {uso_etq}", []))
                continue
            nv = norm(valor)
            comp = [k for k in u.get("compatibles", []) if norm(k) in nv]
            incomp = [k for k in u.get("incompatibles", []) if norm(k) in nv]
            if comp and not incomp:
                hallazgos.append(_h(regla, doc.id, "cumple", f"Uso «{valor}» compatible con {uso_etq} (coincide: {', '.join(comp)})", _ev(c)))
            elif incomp and not comp:
                hallazgos.append(_h(regla, doc.id, "no_cumple", f"Uso «{valor}» incompatible con {uso_etq} (indica: {', '.join(incomp)})", _ev(c)))
            else:
                # caso ambiguo: el LLM opina, pero nunca rechaza por sí solo (precisión > agresividad)
                j = _juicio_llm(f"¿El uso de suelo autorizado «{valor}» permite operar como {uso_etq}?", campos, doc, bitacora)
                evs = _ev(c)
                if j and j.fragmento:
                    evs.append(Evidencia(documento_id=doc.id, pagina=j.pagina or 1, fragmento=j.fragmento))
                if j and j.resultado == "cumple":
                    hallazgos.append(_h(regla, doc.id, "cumple", f"Uso «{valor}» compatible con {uso_etq} según análisis: {j.explicacion}", evs))
                else:
                    exp = j.explicacion if j else "no se pudo determinar automáticamente"
                    hallazgos.append(_h(regla, doc.id, "requiere_revision", f"Compatibilidad de «{valor}» con {uso_etq} no concluyente: {exp}", evs))

        elif t == "anio_pagado":
            anios = [int(a) for a in re.findall(r"\b(19\d{2}|20\d{2})\b", (c.valor if c and c.valor else ""))]
            if not anios:
                fp = campos.get("fecha_pago")
                anios = [int(a) for a in re.findall(r"\b(19\d{2}|20\d{2})\b", fp.valor if fp and fp.valor else "")]
            if not anios:
                hallazgos.append(_h(regla, doc.id, "requiere_revision", "No se pudo determinar el ejercicio pagado", _ev(c)))
                continue
            ultimo, ref = max(anios), fecha_referencia().year
            if ultimo >= ref - regla.get("anios_atraso_max", 0):
                hallazgos.append(_h(regla, doc.id, "cumple", f"Predial pagado al ejercicio {ultimo}", _ev(c)))
            else:
                hallazgos.append(_h(regla, doc.id, falla, f"Último ejercicio pagado {ultimo}; referencia {ref}", _ev(c)))

        elif t == "autoridad_kb":
            if not (c and c.valor):
                continue
            tipo = tipo_cfg["tipo"]
            estado = buscar_kb(tipo, c.valor)
            bitacora.append(f"🔧 leer_kb({tipo!r}) · «{c.valor[:40]}» → {estado}")
            if estado in ("generica", "desconocida"):
                alta = usar("proponer_alta_kb", bitacora, tipo=tipo, entrada=c.valor, fuente=doc.id)
                txt = f"Emisor «{c.valor}» no estaba en la base de conocimiento → alta {alta} (requiere confirmación humana)"
            elif estado == "pendiente":
                txt = f"Emisor «{c.valor}» está en la base como pendiente de confirmar"
            else:
                txt = f"Emisor «{c.valor}» registrado en la base de conocimiento (contexto, no prueba de autenticidad)"
            hallazgos.append(_h(regla, doc.id, "cumple", txt, _ev(c), "info"))

        elif t == "llm_check":
            pregunta = regla["pregunta"].format(uso=uso_etq)
            j = _juicio_llm(pregunta, campos, doc, bitacora)
            evs = [ev for k in regla.get("campos", []) for ev in _ev(campos.get(k))]
            if j and j.fragmento:
                evs.append(Evidencia(documento_id=doc.id, pagina=j.pagina or 1, fragmento=j.fragmento))
            if j is None:
                hallazgos.append(_h(regla, doc.id, "requiere_revision", f"{regla['descripcion']}: no se pudo evaluar automáticamente", evs))
            elif j.resultado == "cumple":
                hallazgos.append(_h(regla, doc.id, "cumple", f"{regla['descripcion']}: {j.explicacion}", evs))
            else:
                # el juicio LLM nunca es más severo que lo que permite la regla
                hallazgos.append(_h(regla, doc.id, falla, f"{regla['descripcion']}: {j.explicacion}", evs))
        else:
            bitacora.append(f"⚠️ Tipo de regla desconocido: {t} ({regla['id']})")
    return hallazgos
