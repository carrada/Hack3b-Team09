"""Traduce el resultado del pipeline multiagente al contrato que consume el frontend tiendas-3b.

Contrato (tiendas-3b/modulo.js): cada PDF se entrega como
    { id, tipo, grupo, archivo, titulo, paginas:[{n,img,w,h}], total_paginas,
      pasos:[{n,pagina,rect,agente,campo,valor,ok,nota,t,confianza}], resumen:{validados,revisar} }
con rect = [x, y, ancho, alto] normalizado (0..1, origen arriba a la izquierda).

Solo LEE el estado que produce `expediente.reporte.ejecutar`; no cambia nada del backend.
"""
from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
from rapidfuzz import fuzz

from expediente.config import NOMBRES_TIPO
from expediente.schemas import Dictamen, Documento, ResultadoDocumento

# tipo del backend -> tipo del frontend
TIPO_FRONT = {"escrituras": "escrituras", "predial": "predial", "alineamiento": "alineamiento", "uso_suelo": "uso"}

# campo del backend -> etiqueta del frontend (las que usan sus reglas y su cruce de datos llevan el nombre exacto)
ETIQUETA = {
    "propietario": "Titular actual",
    "direccion": "Dirección del inmueble",
    "numero_oficial": "Número oficial",
    "clave_catastral": "Clave catastral",
    "lote_manzana": "Identificación del predio",
    "superficie": "Superficie del predio",
    "autoridad_emisora": "Autoridad emisora",
    "uso_autorizado": "Uso de suelo",
    "vigencia": "Vigencia",
    "fecha_emision": "Fecha de expedición",
    "numero_escritura": "Instrumento y volumen",
    "fecha_escritura": "Fecha de otorgamiento",
    "folio_real": "Folio",
    "folio_documento": "Folio",
    "notaria": "Notaría",
    "acto_juridico": "Acto jurídico",
    "curp_rfc_propietario": "CURP / RFC del titular",
    "tipo_persona": "Tipo de persona",
    "colonia": "Colonia",
    "codigo_postal": "Código postal",
    "municipio": "Municipio",
    "superficie_construccion": "Superficie de construcción",
    "periodo_pagado": "Periodo pagado",
    "fecha_pago": "Fecha de pago",
    "alineamiento": "Alineamiento",
    "zonificacion": "Zonificación",
    "restricciones": "Restricciones",
}
# regla del backend -> campo al que se refiere (para marcar ese dato como "revisar" en vez de duplicarlo)
REGLA_CAMPO = {
    "ESC-01": "propietario", "ESC-02": "direccion", "ESC-03": "superficie", "ESC-04": "notaria", "ESC-05": "folio_real",
    "ESC-06": "curp_rfc_propietario", "ESC-07": "notaria",
    "PRE-01": "clave_catastral", "PRE-02": "propietario", "PRE-03": "periodo_pagado", "PRE-04": "curp_rfc_propietario",
    "PRE-05": "autoridad_emisora",
    "ALN-01": "numero_oficial", "ALN-02": "alineamiento", "ALN-03": "vigencia", "ALN-04": "alineamiento",
    "ALN-05": "autoridad_emisora",
    "USO-01": "uso_autorizado", "USO-02": "uso_autorizado", "USO-03": "vigencia", "USO-04": "restricciones",
    "USO-05": "autoridad_emisora",
}
# atributo de la validación cruzada -> campo
CRUCE_CAMPO = {"direccion": "direccion", "propietario": "propietario", "superficie": "superficie",
               "numero_oficial": "numero_oficial", "id_predio": "clave_catastral"}

ANCHO_IMG = 1000  # px de las imágenes de página (como las del frontend)


def etiqueta(campo: str) -> str:
    return ETIQUETA.get(campo, campo.replace("_", " ").capitalize())


# ------------------------------------------------------------------ ubicación del dato en la página (rect)
def _renglones(pagina: fitz.Page) -> list[list[float]]:
    """Renglones de tinta de una página escaneada: franjas horizontales con píxeles oscuros, como [x, y, ancho, alto]
    normalizados. Sirven para ubicar las líneas que transcribió el modelo de visión (que no da coordenadas)."""
    import numpy as np

    escala = 600 / max(pagina.rect.width, 1)
    pix = pagina.get_pixmap(matrix=fitz.Matrix(escala, escala), colorspace=fitz.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    tinta = img < 150
    filas = tinta.mean(axis=1) > 0.004
    bandas, inicio = [], None
    for y, hay in enumerate(list(filas) + [False]):
        if hay and inicio is None:
            inicio = y
        elif not hay and inicio is not None:
            if y - inicio >= 3:  # descarta ruido de un par de píxeles
                if bandas and inicio - bandas[-1][1] <= 2:
                    bandas[-1][1] = y
                else:
                    bandas.append([inicio, y])
            inicio = None
    out = []
    for y0, y1 in bandas:
        cols = np.where(tinta[y0:y1].any(axis=0))[0]
        x0, x1 = (cols.min(), cols.max()) if len(cols) else (0, pix.width)
        out.append([x0 / pix.width, max(y0 - 2, 0) / pix.height, (x1 - x0) / pix.width, (y1 - y0 + 4) / pix.height])
    return out


def _rect_franja(texto: str, fragmento: str, renglones: list[list[float]] | None = None) -> list[float] | None:
    """Páginas leídas por el modelo de visión: se busca la línea transcrita (en orden de lectura) que mejor coincide
    con el fragmento y se lleva al renglón de tinta que le corresponde en la imagen."""
    lineas = [l for l in texto.splitlines() if l.strip()]
    if not lineas or not fragmento:
        return None
    puntos = [fuzz.partial_ratio(fragmento.lower(), l.lower()) for l in lineas]
    i = max(range(len(lineas)), key=puntos.__getitem__)
    if puntos[i] < 70:
        return None
    if renglones:
        j = round(i * (len(renglones) - 1) / max(len(lineas) - 1, 1))
        return [round(v, 4) for v in renglones[min(j, len(renglones) - 1)]]
    alto = max(1 / len(lineas), 0.025)
    y = min(max((i + 0.5) / len(lineas) - alto / 2, 0.0), 1 - alto)
    return [0.06, round(y, 4), 0.88, round(alto, 4)]


def _rect_nativo(pagina: fitz.Page, fragmento: str) -> list[float] | None:
    """PDF con capa de texto: coordenadas exactas buscando el fragmento en la página."""
    for intento in (fragmento[:80], fragmento[:40], fragmento[:20]):
        cajas = pagina.search_for(intento.strip()) if intento.strip() else []
        if cajas:
            r = cajas[0]
            for c in cajas[1:]:
                if abs(c.y0 - r.y1) < 20:  # el fragmento continúa en la línea siguiente
                    r |= c
            W, H = pagina.rect.width, pagina.rect.height
            return [round(r.x0 / W, 4), round(r.y0 / H, 4), round(r.width / W, 4), round(r.height / H, 4)]
    return None


RECT_CABECERA = [0.06, 0.03, 0.88, 0.06]


_RENGLONES: dict[tuple[str, int], list] = {}


def ubicar(doc: Documento, pdf: fitz.Document | None, pagina: int, fragmento: str | None) -> list[float]:
    pag = next((p for p in doc.paginas if p.numero == pagina), None)
    if not fragmento or pag is None:
        return RECT_CABECERA
    valida = pdf is not None and 0 < pagina <= len(pdf)
    if pag.fuente == "nativo" and valida:
        r = _rect_nativo(pdf[pagina - 1], fragmento)
        if r:
            return r
    renglones = None
    if valida:
        clave = (doc.sha256, pagina)
        if clave not in _RENGLONES:
            _RENGLONES[clave] = _renglones(pdf[pagina - 1])
        renglones = _RENGLONES[clave]
    return _rect_franja(pag.texto, fragmento, renglones) or RECT_CABECERA


# ------------------------------------------------------------------ conversión
def _t(n: int) -> str:
    s = n * 0.7
    return f"{int(s // 60):02d}:{s % 60:04.1f}"


def _medidas(pdf: fitz.Document | None, n: int) -> tuple[int, int]:
    if pdf is None or n > len(pdf):
        return ANCHO_IMG, round(ANCHO_IMG * 1.294)
    r = pdf[n - 1].rect
    return ANCHO_IMG, round(ANCHO_IMG * r.height / max(r.width, 1))


def analisis_documento(aid: str, exp: str, nombre_exp: str, doc: Documento, res: ResultadoDocumento | None,
                       discrepancias: list, nombres_docs: dict[str, str]) -> dict:
    """Arma el JSON de un documento: datos extraídos, reglas y validación cruzada como pasos con evidencia."""
    pdf = fitz.open(doc.ruta) if doc.ruta.lower().endswith(".pdf") and Path(doc.ruta).exists() else None
    tipo_b = doc.tipo or "escrituras"
    nombre_tipo = NOMBRES_TIPO.get(tipo_b, tipo_b)
    pasos: list[dict] = []

    def agregar(campo: str, valor: str, pagina: int, fragmento: str | None, ok: bool, agente: str, nota: str = "",
                confianza: float = 1.0):
        pasos.append({"campo": campo, "valor": valor, "pagina": pagina, "rect": ubicar(doc, pdf, pagina, fragmento),
                      "ok": ok, "confianza": round(confianza, 3), "agente": agente, "nota": nota})

    # 1) Recepción: tipo documental
    agregar("Tipo documental", nombre_tipo, 1, None, True, "Recepción",
            f"Clasificado por contenido ({doc.tipo_metodo or 'palabras clave'}, confianza {doc.tipo_confianza:.2f}).")

    # 2) Especialista: cada dato extraído con su evidencia (cita verificada contra el texto leído)
    por_campo: dict[str, dict] = {}
    agente = res.agente if res else f"Especialista {nombre_tipo}"
    if res:
        for c in res.campos:
            if not c.valor:
                continue
            ev = c.evidencia
            ok = bool(ev and ev.verificada)
            agregar(etiqueta(c.nombre), c.valor, ev.pagina if ev else 1, ev.fragmento if ev else None, ok, agente,
                    "" if ok else "La cita de este dato no se encontró literal en el texto del documento.", c.confianza)
            por_campo[c.nombre] = pasos[-1]

        # 3) Reglas del especialista: lo que no cumple marca su dato (o se agrega si el dato no existe)
        for h in res.hallazgos:
            if h.severidad == "info" or h.resultado == "cumple":
                continue
            campo = REGLA_CAMPO.get(h.regla_id)
            nota = f"[{h.regla_id}] {h.descripcion}"
            if campo and campo in por_campo:
                p = por_campo[campo]
                p["ok"] = False
                p["nota"] = (p["nota"] + " " if p["nota"] else "") + nota
            else:
                ev = h.evidencias[0] if h.evidencias else None
                agregar(etiqueta(campo) if campo else h.regla_id,
                        "No consta en el documento" if not ev else ev.fragmento[:120],
                        ev.pagina if ev else 1, ev.fragmento if ev else None, False, agente, nota)
                if campo:
                    por_campo[campo] = pasos[-1]
        if res.error:
            agregar("Extracción", "No se pudo analizar automáticamente", 1, None, False, agente, res.error)

    # 4) Validación cruzada: las discrepancias que involucran a este documento
    for dsc in discrepancias:
        if doc.id not in dsc.valores:
            continue
        otros = "; ".join(f"{nombres_docs.get(k, k)}: «{v}»" for k, v in dsc.valores.items() if k != doc.id)
        nota = f"{dsc.explicacion}" + (f" Otros documentos — {otros}." if otros else "")
        campo = CRUCE_CAMPO.get(dsc.atributo)
        if campo and campo in por_campo:
            p = por_campo[campo]
            p["ok"] = False
            p["agente"] = "Validación cruzada"
            p["nota"] = (p["nota"] + " " if p["nota"] else "") + nota
        else:
            ev = next((e for e in dsc.evidencias if e.documento_id == doc.id), None)
            agregar(etiqueta(campo) if campo else dsc.atributo.replace("_", " ").capitalize(),
                    dsc.valores.get(doc.id, "—"), ev.pagina if ev else 1, ev.fragmento if ev else None, False,
                    "Validación cruzada", nota)

    for i, p in enumerate(pasos, start=1):
        p["n"], p["t"] = i, _t(i)
    n_pag = len(doc.paginas) or (len(pdf) if pdf else 1)
    paginas = []
    for n in range(1, n_pag + 1):
        w, h = _medidas(pdf, n)
        paginas.append({"n": n, "img": f"paginas/{aid}/p{n}.jpg", "w": w, "h": h})
    if pdf is not None:
        pdf.close()
    return {
        "id": aid, "tipo": TIPO_FRONT.get(tipo_b, tipo_b), "grupo": exp, "archivo": doc.nombre_archivo,
        "titulo": f"{nombre_tipo} · {nombre_exp}", "paginas": paginas, "total_paginas": n_pag, "pasos": pasos,
        "resumen": {"validados": sum(p["ok"] for p in pasos), "revisar": sum(not p["ok"] for p in pasos)},
    }


def convertir(exp: str, estado: dict) -> tuple[dict, list[dict]]:
    """Del estado final del grafo a (ficha del expediente, [análisis por documento])."""
    docs = [Documento.model_validate(x) for x in estado.get("documentos", [])]
    resultados = {r["documento_id"]: ResultadoDocumento.model_validate(r)
                  for r in estado.get("resultados_verificados") or estado.get("resultados", [])}
    dic = Dictamen.model_validate(estado["dictamen"]) if estado.get("dictamen") else None
    nombres = {d.id: NOMBRES_TIPO.get(d.tipo or "", d.nombre_archivo) for d in docs}

    # dirección legible para el nombre del expediente y para ubicarlo en el mapa
    def dato(campo: str) -> str | None:
        for tipo in ("escrituras", "predial", "alineamiento", "uso_suelo"):
            for r in resultados.values():
                if r.tipo == tipo and (c := r.campo(campo)):
                    return c.valor
        return None

    direccion, municipio = dato("direccion"), dato("municipio")
    nombre = direccion or exp
    # texto para el geocodificador del mapa: dirección + colonia/municipio si la dirección no los trae ya
    partes = [direccion] if direccion else []
    for extra in (dato("colonia"), municipio):
        if extra and not any(fuzz.partial_ratio(extra.lower(), p.lower()) >= 90 for p in partes):
            partes.append(extra)
    ficha = {"id": exp, "nombre": nombre, "municipio": municipio or "", "busqueda": ", ".join(partes) or None,
             "coords": None, "sintetico": False, "docs": {}, "extras": []}

    analisis = []
    vistos: set[str] = set()
    for d in docs:  # un análisis por tipo; si llegan dos del mismo tipo, el segundo queda como extra
        tipo_f = TIPO_FRONT.get(d.tipo or "", "escrituras")
        aid = f"{exp}-{tipo_f}" if tipo_f not in vistos else f"{exp}-{tipo_f}-{d.sha256[:6]}"
        a = analisis_documento(aid, exp, nombre, d, resultados.get(d.id), dic.discrepancias if dic else [], nombres)
        a["_ruta"] = d.ruta  # interno (para renderizar páginas); no se envía al navegador
        a["bytes"] = Path(d.ruta).stat().st_size if Path(d.ruta).exists() else 0
        analisis.append(a)
        if tipo_f in vistos:
            ficha["extras"].append(aid)
        else:
            vistos.add(tipo_f)
            ficha["docs"][tipo_f] = aid
    if dic:
        ficha["dictamen"] = {"recomendacion": dic.recomendacion, "confianza": dic.confianza, "resumen": dic.resumen,
                             "razones": dic.razones, "faltantes": dic.documentos_faltantes,
                             "descartados": dic.documentos_descartados}
    return ficha, analisis
