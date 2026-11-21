"""[1] Agente de Recepción.

- Descarta lo que no es documento (formatos no soportados, sin texto, fotos/INE/CURP sueltas).
- OCR / extracción de texto (paso de pipeline local con caché).
- Clasifica el tipo POR CONTENIDO: puntaje por palabras clave (YAML) + LLM; si difieren, gana el LLM con menor confianza.
- Extrae una "huella" (dirección, propietario, clave) para agrupar por inmueble.
- Detecta faltantes.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..config import NOMBRES_TIPO, TIPOS, cfg, llm_estructurado, reglas
from ..ocr import EXT_IMG, EXT_PDF, extraer_texto
from ..schemas import ClasificacionLLM, Documento, ExpedienteState
from ..tools import clave_normalizada, comparar_direcciones, comparar_nombres, norm


def puntaje_palabras(doc: Documento) -> dict[str, float]:
    """Palabras clave del YAML; la primera página pesa triple (las escrituras mencionan 'predial' en cláusulas)."""
    p1 = norm(doc.paginas[0].texto) if doc.paginas else ""
    resto = norm(" ".join(p.texto for p in doc.paginas[1:6]))
    puntajes = {}
    for tipo in TIPOS:
        kws = [norm(k) for k in reglas(tipo)["clasificacion"]["palabras_clave"]]
        puntajes[tipo] = sum(3 * (k in p1) + (k in resto) for k in kws) / (4 * len(kws))
    return puntajes


def clasificar(doc: Documento, bitacora: list[str]) -> Documento:
    pk = puntaje_palabras(doc)
    tipo_kw = max(pk, key=pk.get)
    texto = doc.texto_con_paginas()[:7000]
    prompt = (
        "Eres el agente de Recepción de expedientes inmobiliarios (México). Clasifica el documento por su CONTENIDO, "
        "no por el nombre del archivo:\n"
        "- escrituras: escritura pública / instrumento notarial de propiedad\n"
        "- predial: boleta, recibo o estado de cuenta del impuesto predial\n"
        "- alineamiento: constancia de alineamiento y/o número oficial\n"
        "- uso_suelo: licencia, constancia, dictamen o factibilidad de uso de suelo\n"
        "- otro: cualquier otra cosa (INE, CURP suelta, foto, plano sin texto legal, etc.)\n"
        "Extrae también, si aparecen, la dirección del inmueble, el propietario/contribuyente y la clave catastral.\n\n"
        f"Archivo: {doc.nombre_archivo}\n\n{texto}"
    )
    try:
        r = llm_estructurado(ClasificacionLLM).invoke(prompt)
    except Exception as e:  # noqa: BLE001 - sin LLM, se usa solo palabras clave
        bitacora.append(f"⚠️ Recepción: LLM no disponible para {doc.nombre_archivo} ({e}); uso palabras clave")
        r = None

    upd: dict = {}
    if r is not None and (not r.es_documento_legal or r.tipo == "otro") and pk[tipo_kw] < 0.25:
        upd = {"descartado": True, "motivo_descarte": f"No es un documento del expediente: {r.motivo}"}
    elif r is not None and r.tipo != "otro":
        coincide = r.tipo == tipo_kw
        upd = {"tipo": r.tipo, "tipo_metodo": "llm+palabras_clave" if coincide else "llm",
               "tipo_confianza": 0.95 if coincide else 0.7,
               "huella": {"direccion": r.direccion, "propietario": r.propietario, "clave_catastral": r.clave_catastral}}
    elif pk[tipo_kw] >= 0.1:
        upd = {"tipo": tipo_kw, "tipo_metodo": "palabras_clave", "tipo_confianza": round(min(0.9, 0.4 + pk[tipo_kw]), 2)}
    else:
        upd = {"descartado": True, "motivo_descarte": "No se pudo identificar el tipo de documento"}
    doc = doc.model_copy(update=upd)
    if doc.descartado:
        bitacora.append(f"🗑️ Recepción: {doc.nombre_archivo} descartado — {doc.motivo_descarte}")
    else:
        bitacora.append(f"📄 Recepción: {doc.nombre_archivo} → {NOMBRES_TIPO[doc.tipo]} "
                        f"({doc.tipo_metodo}, conf {doc.tipo_confianza:.2f}, {len(doc.paginas)} pág., OCR {doc.calidad:.2f})")
    return doc


def mismo_inmueble_huella(a: dict, b: dict) -> bool:
    ca, cb = clave_normalizada(a.get("clave_catastral")), clave_normalizada(b.get("clave_catastral"))
    if len(ca) >= 6 and ca == cb:
        return True
    if a.get("direccion") and b.get("direccion"):
        sd = comparar_direcciones.invoke({"a": a["direccion"], "b": b["direccion"]})
        if sd >= 85:
            return True
        if sd >= 70 and a.get("propietario") and b.get("propietario"):
            return comparar_nombres.invoke({"a": a["propietario"], "b": b["propietario"]}) >= 85
    return False


def agrupar(docs: list[Documento]) -> list[Documento]:
    """Union-find sobre la huella. El propietario solo no basta (un dueño puede tener varios inmuebles)."""
    padre = list(range(len(docs)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            if mismo_inmueble_huella(docs[i].huella, docs[j].huella):
                padre[raiz(i)] = raiz(j)
    ids: dict[int, int] = {}
    salida = []
    for i, d in enumerate(docs):
        g = ids.setdefault(raiz(i), len(ids) + 1)
        salida.append(d.model_copy(update={"grupo": g}))
    return salida


def preparar_documentos(archivos: list[str], bitacora: list[str]) -> tuple[list[Documento], list[Documento]]:
    """OCR + clasificación + agrupación. Reutilizado por el grafo y por el modo lote (cli)."""
    aceptados, descartados, vistos = [], [], {}
    usados: set[str] = set()

    def procesar(ruta: str) -> Documento:
        p = Path(ruta)
        base_id = re.sub(r"[^\w\-]+", "_", p.stem)[:50]
        if p.suffix.lower() not in EXT_PDF | EXT_IMG:
            return Documento(id=base_id, nombre_archivo=p.name, ruta=str(p), sha256="", descartado=True,
                             motivo_descarte=f"Formato no soportado ({p.suffix})")
        doc = extraer_texto(p, base_id)
        if sum(len(pg.texto.strip()) for pg in doc.paginas) < 40:
            return doc.model_copy(update={"descartado": True, "motivo_descarte": "Sin texto legible (posible foto o escaneo ilegible)"})
        return clasificar(doc, bitacora)

    with ThreadPoolExecutor(max_workers=3) as ex:
        docs = list(ex.map(procesar, archivos))

    for d in docs:
        if d.id in usados:
            d = d.model_copy(update={"id": f"{d.id}_{d.sha256[:6]}"})
        usados.add(d.id)
        if d.sha256 and d.sha256 in vistos and not d.descartado:
            d = d.model_copy(update={"descartado": True, "motivo_descarte": f"Duplicado de {vistos[d.sha256]}"})
        if d.descartado:
            descartados.append(d)
            if "Formato" in d.motivo_descarte or "Sin texto" in d.motivo_descarte:
                bitacora.append(f"🗑️ Recepción: {d.nombre_archivo} descartado — {d.motivo_descarte}")
        else:
            vistos[d.sha256] = d.nombre_archivo
            aceptados.append(d)
    return agrupar(aceptados), descartados


def nodo_recepcion(state: ExpedienteState) -> dict:
    bitacora: list[str] = ["━━ [1] Recepción: OCR, clasificación por contenido y agrupación"]
    aceptados, descartados = preparar_documentos(state["archivos"], bitacora)
    tipos_presentes = {d.tipo for d in aceptados}
    faltan = [NOMBRES_TIPO[t] for t in cfg()["documentos_requeridos"] if t not in tipos_presentes]
    grupos = {d.grupo for d in aceptados}
    if len(grupos) > 1:
        bitacora.append(f"🏠 Recepción: la huella sugiere {len(grupos)} inmuebles distintos; el Validador cruzado lo confirmará")
    bitacora.append(f"📋 Recepción: {len(aceptados)} documentos aceptados, {len(descartados)} descartados; "
                    f"faltantes: {', '.join(faltan) or 'ninguno'}")
    return {"documentos": [d.model_dump() for d in aceptados],
            "descartados": [d.model_dump() for d in descartados], "bitacora": bitacora}
