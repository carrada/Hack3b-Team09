"""[6] Validador cruzado. Corre SIEMPRE, aunque falten documentos o un especialista falle.

Normaliza y compara entre documentos: dirección, número oficial, propietario, superficie e
identificación del predio. Reglas + fuzzy matching; el LLM solo desempata direcciones ambiguas.
Cada discrepancia guarda qué documentos, el valor en cada uno y la evidencia.
"""
from __future__ import annotations

from ..config import cfg, llm_estructurado
from ..schemas import Cruce, Discrepancia, ExpedienteState, MismoInmuebleLLM, ResultadoDocumento
from ..tools import clave_normalizada, numero_oficial_normalizado, usar

PRIORIDAD = ["escrituras", "predial", "alineamiento", "uso_suelo"]


def _ev(r: ResultadoDocumento, campo: str):
    c = r.campo(campo)
    return [c.evidencia] if c and c.evidencia else []


def _llm_mismo_inmueble(a: str, b: str, bitacora: list[str]) -> MismoInmuebleLLM | None:
    try:
        r = llm_estructurado(MismoInmuebleLLM).invoke(
            "Dos documentos de un expediente inmobiliario en México describen la ubicación así.\n"
            f"A: {a}\nB: {b}\n¿Se refieren al MISMO inmueble? Considera abreviaturas, variantes de escritura, "
            "letras en el número (12 vs 12-A puede ser otro predio), errores de lectura y referencias de lote/manzana.")
        bitacora.append(f"🧠 Validador: dirección ambigua → LLM: {'mismo' if r.mismo else 'distinto'} inmueble")
        return r
    except Exception as e:  # noqa: BLE001
        bitacora.append(f"⚠️ Validador: LLM no disponible para desempate ({e})")
        return None


def validar(resultados: list[ResultadoDocumento], grupos: dict[str, int], bitacora: list[str]):
    vc = cfg()["validacion_cruzada"]
    rs = sorted(resultados, key=lambda r: PRIORIDAD.index(r.tipo))
    cruces: list[Cruce] = []
    discrepancias: list[Discrepancia] = []
    senales_otro: dict[str, list[str]] = {r.documento_id: [] for r in rs}
    coincidencias_fuertes: dict[str, int] = {r.documento_id: 0 for r in rs}

    def con(campo):
        return [r for r in rs if r.campo(campo)]

    # ---- dirección
    docs = con("direccion")
    if len(docs) >= 2:
        ancla = docs[0]
        for r in docs[1:]:
            a, b = ancla.campo("direccion").valor, r.campo("direccion").valor
            s = usar("comparar_direcciones", bitacora, a=a, b=b)
            vals = {ancla.documento_id: a, r.documento_id: b}
            if s >= vc["direccion_igual"]:
                cruces.append(Cruce(atributo="direccion", valores=vals, score=s, resultado="coincide", metodo="fuzzy"))
                coincidencias_fuertes[r.documento_id] += 1
                continue
            metodo, exp, mismo = "fuzzy", f"Similitud {s:.0f}/100", False
            if s >= vc["direccion_ambigua"]:
                j = _llm_mismo_inmueble(a, b, bitacora)
                if j:
                    metodo, exp, mismo = "llm", j.explicacion, j.mismo
            if mismo:
                cruces.append(Cruce(atributo="direccion", valores=vals, score=s, resultado="coincide", metodo=metodo, explicacion=exp))
                discrepancias.append(Discrepancia(
                    atributo="direccion", valores=vals, severidad="menor", evidencias=_ev(ancla, "direccion") + _ev(r, "direccion"),
                    explicacion=f"La dirección se escribe distinto pero parece el mismo inmueble ({exp}). Confirmar."))
            else:
                cruces.append(Cruce(atributo="direccion", valores=vals, score=s, resultado="difiere", metodo=metodo, explicacion=exp))
                discrepancias.append(Discrepancia(
                    atributo="direccion", valores=vals, severidad="menor", evidencias=_ev(ancla, "direccion") + _ev(r, "direccion"),
                    explicacion=f"Direcciones distintas entre {ancla.tipo} y {r.tipo}: {exp}"))
                if s < vc["direccion_ambigua"] or metodo == "llm":
                    senales_otro[r.documento_id].append(f"dirección distinta ({s:.0f}/100)")

    # ---- número oficial (campo propio o extraído de la dirección)
    nums = {}
    for r in rs:
        c = r.campo("numero_oficial") or r.campo("direccion")
        n = numero_oficial_normalizado(c.valor) if c else ""
        if n:
            nums[r.documento_id] = (n, c, r)
    if len(nums) >= 2:
        base_id = next((r.documento_id for r in rs if r.tipo == "alineamiento" and r.documento_id in nums), next(iter(nums)))
        bn = nums[base_id][0]
        vals = {did: c.valor for did, (n, c, r) in nums.items()}
        distintos = {did for did, (n, _, _) in nums.items() if n != bn}
        for did, (n, c, r) in nums.items():
            if did != base_id:
                cruces.append(Cruce(atributo="numero_oficial", valores={base_id: nums[base_id][1].valor, did: c.valor},
                                    score=100 if n == bn else 0, resultado="coincide" if n == bn else "difiere",
                                    metodo="exacto", explicacion="" if n == bn else f"{bn} ≠ {n}"))
        if distintos:
            discrepancias.append(Discrepancia(
                atributo="numero_oficial", valores=vals, severidad="menor",
                evidencias=[c.evidencia for _, c, _ in nums.values() if c.evidencia],
                explicacion="El número oficial no coincide entre documentos: " +
                            ", ".join(f"{nums[d][2].tipo}={nums[d][0]}" for d in nums)))

    # ---- propietario: escritura ↔ predial (en alineamiento/uso de suelo suele aparecer el solicitante)
    esc = [r for r in con("propietario") if r.tipo == "escrituras"]
    pre = [r for r in con("propietario") if r.tipo == "predial"]
    if esc and pre:
        a = esc[0].campo("propietario").valor
        for r in pre:
            b = r.campo("propietario").valor
            s = usar("comparar_nombres", bitacora, a=a, b=b)
            vals = {esc[0].documento_id: a, r.documento_id: b}
            if s >= vc["nombre_igual"]:
                cruces.append(Cruce(atributo="propietario", valores=vals, score=s, resultado="coincide", metodo="fuzzy"))
            else:
                res = "ambiguo" if s >= vc["nombre_ambiguo"] else "difiere"
                cruces.append(Cruce(atributo="propietario", valores=vals, score=s, resultado=res, metodo="fuzzy"))
                discrepancias.append(Discrepancia(
                    atributo="propietario", valores=vals, severidad="menor",
                    evidencias=_ev(esc[0], "propietario") + _ev(r, "propietario"),
                    explicacion=("Nombre parcialmente distinto (¿variante o error de lectura?)" if res == "ambiguo" else
                                 "El predial está a nombre de otra persona distinta al titular de la escritura "
                                 "(p. ej. propietario anterior): requiere revisión, no es rechazo")))

    # ---- superficie
    docs = [r for r in con("superficie")]
    if len(docs) >= 2:
        ancla = docs[0]
        for r in docs[1:]:
            a, b = ancla.campo("superficie").valor, r.campo("superficie").valor
            comp = usar("comparar_superficies", bitacora, a=a, b=b, tolerancia=vc["superficie_tolerancia_menor"])
            vals = {ancla.documento_id: a, r.documento_id: b}
            if not comp["comparable"]:
                continue
            dif = comp["diferencia_rel"]
            if comp["dentro_tolerancia"]:
                cruces.append(Cruce(atributo="superficie", valores=vals, score=round(100 * (1 - dif), 1), resultado="coincide", metodo="numerico"))
                coincidencias_fuertes[r.documento_id] += 1
                continue
            if r.tipo == "uso_suelo" and comp["b_m2"] < comp["a_m2"]:
                cruces.append(Cruce(atributo="superficie", valores=vals, score=round(100 * (1 - dif), 1), resultado="coincide",
                                    metodo="numerico", explicacion="El uso de suelo aplica a una superficie menor que el terreno (válido)"))
                continue
            cruces.append(Cruce(atributo="superficie", valores=vals, score=round(100 * (1 - dif), 1), resultado="difiere",
                                metodo="numerico", explicacion=f"Diferencia {dif:.1%}"))
            discrepancias.append(Discrepancia(
                atributo="superficie", valores=vals, severidad="menor", evidencias=_ev(ancla, "superficie") + _ev(r, "superficie"),
                explicacion=f"Superficie {comp['a_m2']:,.2f} m² ({ancla.tipo}) vs {comp['b_m2']:,.2f} m² ({r.tipo}): "
                            f"diferencia {dif:.1%} (tolerancia {vc['superficie_tolerancia_menor']:.0%})"))
            if dif > vc["superficie_tolerancia_critica"]:
                senales_otro[r.documento_id].append(f"superficie {dif:.0%} distinta")

    # ---- identificación del predio (clave catastral / cuenta predial)
    docs = [r for r in con("clave_catastral") if len(clave_normalizada(r.campo("clave_catastral").valor)) >= 5]
    if len(docs) >= 2:
        ancla = next((r for r in docs if r.tipo == "predial"), docs[0])
        ka = clave_normalizada(ancla.campo("clave_catastral").valor)
        from rapidfuzz import fuzz
        for r in docs:
            if r is ancla:
                continue
            kb = clave_normalizada(r.campo("clave_catastral").valor)
            s = float(fuzz.ratio(ka, kb))
            vals = {ancla.documento_id: ancla.campo("clave_catastral").valor, r.documento_id: r.campo("clave_catastral").valor}
            if s >= vc["clave_igual"] or (min(len(ka), len(kb)) >= 6 and (ka in kb or kb in ka)):
                cruces.append(Cruce(atributo="id_predio", valores=vals, score=s, resultado="coincide", metodo="exacto" if s == 100 else "fuzzy"))
                coincidencias_fuertes[r.documento_id] += 2
            else:
                cruces.append(Cruce(atributo="id_predio", valores=vals, score=s, resultado="difiere", metodo="fuzzy"))
                discrepancias.append(Discrepancia(
                    atributo="id_predio", valores=vals, severidad="menor",
                    evidencias=_ev(ancla, "clave_catastral") + _ev(r, "clave_catastral"),
                    explicacion="La clave catastral/cuenta no coincide (puede ser otra nomenclatura o un error de lectura)"))
                senales_otro[r.documento_id].append("clave catastral distinta")

    # ---- ¿documentos de otro inmueble? (≥2 señales independientes y sin coincidencias fuertes)
    principal = max(set(grupos.values()), key=list(grupos.values()).count) if grupos else None
    for r in rs:
        s = list(senales_otro[r.documento_id])
        if principal is not None and grupos.get(r.documento_id) not in (None, principal):
            s.append("la huella de Recepción lo agrupa con otro inmueble")
        if len(s) >= 2 and coincidencias_fuertes[r.documento_id] == 0:
            evs = [e for campo in ("direccion", "clave_catastral", "superficie") for e in _ev(r, campo)]
            discrepancias.append(Discrepancia(
                atributo="otro_inmueble", valores={r.documento_id: r.nombre_archivo}, severidad="critica", evidencias=evs,
                explicacion=f"El documento {r.nombre_archivo} ({r.tipo}) parece corresponder a OTRO inmueble: {'; '.join(s)}"))
            bitacora.append(f"🚩 Validador: {r.documento_id} parece de otro inmueble ({'; '.join(s)})")

    # las discrepancias menores de un documento "de otro inmueble" quedan subsumidas en la crítica
    otros = {d.valores and next(iter(d.valores)) for d in discrepancias if d.atributo == "otro_inmueble"}
    if otros:
        limpias = []
        for d in discrepancias:
            if d.atributo != "otro_inmueble" and set(d.valores) & otros:
                resto = {k: v for k, v in d.valores.items() if k not in otros}
                if d.atributo != "numero_oficial" or len(set(numero_oficial_normalizado(v) for v in resto.values())) < 2:
                    continue
                d = d.model_copy(update={
                    "valores": resto, "evidencias": [e for e in d.evidencias if e.documento_id not in otros],
                    "explicacion": "El número oficial no coincide entre documentos: " +
                                   ", ".join(f"{k}={numero_oficial_normalizado(v)}" for k, v in resto.items())})
            limpias.append(d)
        discrepancias = limpias
    return cruces, discrepancias


def nodo_validador_cruzado(state: ExpedienteState) -> dict:
    bitacora = ["━━ [6] Validador cruzado: dirección, número oficial, propietario, superficie, id. del predio"]
    resultados = [ResultadoDocumento.model_validate(r) for r in state.get("resultados", [])]
    grupos = {d["id"]: d.get("grupo") for d in state.get("documentos", [])}
    if len(resultados) < 2:
        bitacora.append("ℹ️ Validador: menos de 2 documentos analizados; no hay cruces posibles")
        return {"cruces": [], "discrepancias": [], "bitacora": bitacora}
    cruces, discrepancias = validar(resultados, grupos, bitacora)
    bitacora.append(f"📊 Validador: {len(cruces)} cruces, {sum(c.resultado == 'coincide' for c in cruces)} coinciden, "
                    f"{len(discrepancias)} discrepancias")
    return {"cruces": [c.model_dump() for c in cruces], "discrepancias": [d.model_dump() for d in discrepancias], "bitacora": bitacora}
