"""[2-5] Agentes especialistas (Escrituras, Predial, Alineamiento, Uso de suelo).

Mismo esqueleto, distinta configuración: los campos y reglas salen de config/reglas/<tipo>.yaml,
así que cambiar las reglas oficiales no requiere tocar prompts ni código.
Cada uno:
  1. extrae campos con structured output: {valor, página, fragmento literal}
  2. evalúa las reglas del YAML (herramientas deterministas; LLM solo en reglas llm_check / ambiguas)
  3. consulta su base de conocimiento MD
  4. devuelve Cumple / Requiere revisión / No cumple + motivos (siempre)
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from ..config import NOMBRES_TIPO, cfg, llm_estructurado, reglas
from ..rules import evaluar
from ..schemas import (Campo, Documento, EnvioEspecialista, Evidencia, ExtraccionLLM, Hallazgo,
                       ResultadoDocumento, peor)

INSTRUCCIONES = """Eres el agente especialista en «{nombre}» de un equipo legal que revisa expedientes inmobiliarios en México.
Extrae del documento ÚNICAMENTE la información que aparece en él. Reglas:
- Devuelve un elemento por cada campo solicitado, con el mismo nombre.
- 'fragmento' debe ser una copia LITERAL (tal como está, incluso con errores de OCR) de 10 a 200 caracteres del texto que sustenta el valor, y 'pagina' el número del marcador === PÁGINA n === donde aparece.
- Si un campo no aparece, valor=null, fragmento=null. No inventes ni deduzcas datos ausentes.
- En 'direccion' pon la dirección COMPLETA (calle, número, colonia, municipio) tal como aparece.
- Fechas en 'valor' como AAAA-MM-DD cuando sea posible. Superficies con su unidad.
- En 'observaciones' anota riesgos visibles: ilegibilidad, tachaduras, falta de firmas/sellos, datos contradictorios dentro del documento.

Campos a extraer:
{campos}
"""


def extraer(doc: Documento, tipo_cfg: dict) -> tuple[dict[str, Campo], list[str]]:
    lista = "\n".join(f"- {c['nombre']}{' (obligatorio)' if c.get('obligatorio') else ''}: {c['descripcion']}"
                      for c in tipo_cfg["campos"])
    sistema = INSTRUCCIONES.format(nombre=tipo_cfg["nombre"], campos=lista)
    texto = doc.texto_con_paginas(cfg()["ocr"]["max_chars_por_documento"])
    r: ExtraccionLLM = llm_estructurado(ExtraccionLLM).invoke(
        [("system", sistema), ("human", f"Documento: {doc.id}\n\n{texto}")])
    calidad_pag = {p.numero: p.calidad for p in doc.paginas}
    campos: dict[str, Campo] = {}
    for c in r.campos:
        if c.nombre in campos and campos[c.nombre].valor:
            continue
        ev = None
        if c.valor and c.fragmento:
            ev = Evidencia(documento_id=doc.id, pagina=c.pagina or 1, fragmento=c.fragmento)
        conf = 0.0
        if c.valor:
            conf = calidad_pag.get(c.pagina or 1, doc.calidad) * (1.0 if ev else 0.6)
        campos[c.nombre] = Campo(nombre=c.nombre, valor=c.valor, evidencia=ev, confianza=round(conf, 3))
    for c in tipo_cfg["campos"]:  # garantiza todos los campos aunque el LLM omita alguno
        campos.setdefault(c["nombre"], Campo(nombre=c["nombre"]))
    return campos, r.observaciones


def analizar_documento(doc: Documento, tipo: str, uso: str, bitacora: list[str]) -> ResultadoDocumento:
    tcfg = reglas(tipo)
    agente = f"Especialista {NOMBRES_TIPO[tipo]}"
    oblig = [c["nombre"] for c in tcfg["campos"] if c.get("obligatorio")]
    try:
        campos, observaciones = extraer(doc, tcfg)
        if oblig and not any(campos[n].valor for n in oblig):
            bitacora.append(f"↻ {agente}: extracción vacía en {doc.id}, reintentando")
            campos, observaciones = extraer(doc, tcfg)
    except Exception as e:  # noqa: BLE001 - el flujo NO se corta: el resultado queda en revisión
        bitacora.append(f"⚠️ {agente}: falló la extracción de {doc.id}: {e}")
        return ResultadoDocumento(
            documento_id=doc.id, nombre_archivo=doc.nombre_archivo, tipo=tipo, agente=agente, campos=[],
            hallazgos=[Hallazgo(regla_id="EXTRACCION", documento_id=doc.id, severidad="critica",
                                resultado="requiere_revision", descripcion=f"No se pudo extraer información: {e}")],
            estado="requiere_revision", motivos=["No se pudo extraer la información automáticamente; revisar manualmente"],
            obligatorios_total=len(oblig), calidad_ocr=doc.calidad, error=str(e))

    encontrados = sum(1 for n in oblig if campos[n].valor)
    bitacora.append(f"🔎 {agente}: {doc.id} — {encontrados}/{len(oblig)} campos obligatorios extraídos")
    hallazgos = evaluar(tcfg, campos, doc, uso, bitacora)
    for o in observaciones:
        hallazgos.append(Hallazgo(regla_id="OBS", documento_id=doc.id, severidad="info", resultado="cumple",
                                  descripcion=f"Observación del agente: {o}"))
    if doc.calidad < 0.6:
        hallazgos.append(Hallazgo(regla_id="OCR", documento_id=doc.id, severidad="menor", resultado="requiere_revision",
                                  descripcion=f"Calidad de OCR baja ({doc.calidad:.0%}); los valores pueden tener errores"))

    evaluables = [h for h in hallazgos if h.severidad != "info"]
    estado = peor(*[h.resultado for h in evaluables]) if evaluables else "requiere_revision"
    motivos = [f"{'✔' if h.resultado == 'cumple' else ('✖' if h.resultado == 'no_cumple' else '⚠')} "
               f"[{h.regla_id}] {h.descripcion}" for h in hallazgos if h.regla_id != "OBS"]
    return ResultadoDocumento(
        documento_id=doc.id, nombre_archivo=doc.nombre_archivo, tipo=tipo, agente=agente,
        campos=list(campos.values()), hallazgos=hallazgos, estado=estado, motivos=motivos,
        reglas_evaluadas=len(evaluables), reglas_pasan=sum(h.resultado == "cumple" for h in evaluables),
        obligatorios_total=len(oblig), obligatorios_encontrados=encontrados, calidad_ocr=doc.calidad)


def crear_especialista(tipo: str):
    def nodo(envio: EnvioEspecialista) -> dict:
        bitacora = [f"━━ Especialista {NOMBRES_TIPO[tipo]}: {len(envio['documentos'])} documento(s)"]
        docs = [Documento.model_validate(d) for d in envio["documentos"]]
        with ThreadPoolExecutor(max_workers=3) as ex:
            res = list(ex.map(lambda d: analizar_documento(d, tipo, envio["uso_requerido"], bitacora), docs))
        for r in res:
            bitacora.append(f"   ↳ {r.documento_id}: {r.estado}")
        return {"resultados": [r.model_dump() for r in res], "bitacora": bitacora}

    nodo.__name__ = f"especialista_{tipo}"
    return nodo
