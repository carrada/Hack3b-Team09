"""Prototipo · Revisión de expedientes inmobiliarios (Reto 1 · Hackatón Tiendas 3B).

    streamlit run app.py
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pymupdf as fitz
import streamlit as st
from langgraph.types import Command

from expediente.config import DIR_CACHE, NOMBRES_TIPO, cfg, modelos_ollama, soporta_vision
from expediente.graph import construir_grafo
from expediente.reporte import markdown
from expediente.schemas import ETIQUETA, ICONO, Cruce, Dictamen, Documento, ResultadoDocumento

st.set_page_config(page_title="Expedientes 3B · Revisión multiagente", page_icon="📑", layout="wide")

COLOR = {"cumple": "#1b873f", "requiere_revision": "#b7791f", "no_cumple": "#c53030"}


@st.cache_resource
def grafo():
    return construir_grafo()


def render_pagina(ruta: str, pagina: int, fragmento: str | None) -> bytes | None:
    """Renderiza la página citada y resalta el fragmento si el PDF tiene capa de texto."""
    try:
        doc = fitz.open(ruta)
        if pagina < 1 or pagina > len(doc):
            return None
        p = doc[pagina - 1]
        if fragmento:
            for linea in [x.strip() for x in fragmento.splitlines() if len(x.strip()) > 5][:4] or [fragmento[:60]]:
                for rect in p.search_for(linea[:80]):
                    p.add_highlight_annot(rect)
        return p.get_pixmap(dpi=110).tobytes("png")
    except Exception:  # noqa: BLE001
        return None


def mostrar_evidencia(ev: dict | None, docs: dict[str, Documento], clave: str):
    if not ev:
        st.caption("Sin evidencia citada")
        return
    marca = "✔ verificada en OCR" if ev.get("verificada") else "✖ no encontrada literal en el OCR"
    st.markdown(f"**{ev['documento_id']}** · pág. {ev['pagina']} · {marca} ({ev.get('score_verificacion', 0):.0f})")
    st.code(ev["fragmento"], language=None)
    d = docs.get(ev["documento_id"])
    if d and st.toggle("Ver página original", key=clave):
        img = render_pagina(d.ruta, ev["pagina"], ev["fragmento"])
        if img:
            st.image(img)


def mostrar_diagrama():
    """Dibuja el grafo de agentes: PNG (cacheado) y, si no hay red, Mermaid renderizado en el navegador."""
    import streamlit.components.v1 as components

    png = DIR_CACHE / "grafo.png"
    g = grafo().get_graph()
    if not png.exists():
        try:
            png.parent.mkdir(parents=True, exist_ok=True)
            png.write_bytes(g.draw_mermaid_png())
        except Exception:  # noqa: BLE001 - sin red para mermaid.ink
            png = None
    if png and png.exists():
        st.image(str(png), width="stretch")
    else:
        codigo = g.draw_mermaid().replace("`", "'")
        components.html(
            f"<pre class='mermaid'>{codigo}</pre>"
            "<script type='module'>import m from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';"
            "m.initialize({startOnLoad:true});</script>", height=700, scrolling=True)
    with st.popover("Ver código Mermaid"):
        st.code(g.draw_mermaid(), language="text")


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("⚙️ Expediente")
    usos = cfg()["usos_requeridos"]
    uso = st.radio("Uso requerido", list(usos), format_func=lambda k: usos[k]["etiqueta"])
    hitl = st.checkbox("Human in the loop", value=True, help="Pausa el flujo para que una persona confirme cuando no es 'Cumple'")
    st.markdown("**Modelo de lenguaje (agentes)**")
    prov = st.radio("Proveedor", ["openai", "ollama"], index=0 if os.getenv("LLM_PROVIDER", "openai") == "openai" else 1,
                    format_func=lambda m: {"openai": "OpenAI (nube)", "ollama": "Ollama (local)"}[m])
    os.environ["LLM_PROVIDER"] = prov
    if prov == "ollama":
        instalados = modelos_ollama()
        if instalados:
            actual = os.getenv("OLLAMA_MODEL", "mistral:latest")
            os.environ["OLLAMA_MODEL"] = st.selectbox("Modelo local", instalados,
                                                      index=instalados.index(actual) if actual in instalados else 0)
        else:
            st.error("Ollama no responde en localhost:11434. Inícialo con `ollama serve` e instala un modelo "
                     "(`ollama pull qwen2.5:7b`).")
        st.info("**Ollama (local)**\n\n"
                "✅ Sin costo por llamada y sin enviar texto a servicios externos.\n\n"
                "⚠️ Mucho más lento en equipos sin GPU (minutos por documento).\n\n"
                "⚠️ Los modelos pequeños (≤3B) extraen peor y citan fragmentos que luego no se verifican: "
                "habrá más 'Requiere revisión'. Se recomienda ≥7B.\n\n"
                "⚠️ Si falla el formato estructurado, el especialista queda en revisión manual.", icon="🖥️")
    else:
        st.warning("**OpenAI (nube)**\n\n"
                   "✅ Más rápido y más preciso en extracción.\n\n"
                   "⚠️ El texto de los documentos se envía a la API y tiene costo por uso.\n\n"
                   "⚠️ Requiere conexión a internet y `OPENAI_API_KEY`.", icon="☁️")
    motor = st.radio("Motor OCR", ["tesseract", "vision"], index=0 if os.getenv("OCR_MOTOR", "tesseract") == "tesseract" else 1,
                     format_func=lambda m: {"tesseract": "Tesseract (sin IA)", "vision": "Visión (IA)"}[m],
                     help="Tesseract corre local sin IA. Visión usa el LLM para leer la imagen (mejor en escaneos difíciles).")
    os.environ["OCR_MOTOR"] = motor
    if motor == "vision" and not soporta_vision():
        st.error("El modelo local elegido no es multimodal: Visión caerá a Tesseract. "
                 "Usa un modelo con visión (p. ej. `llava`, `qwen2.5vl`) o cambia a OpenAI.")
    if motor == "tesseract":
        st.info(
            "**Tesseract (sin IA, local)**\n\n"
            "✅ Gratis, rápido y reproducible; las imágenes no salen de tu equipo.\n\n"
            "✅ Cada palabra trae su confianza real, que alimenta la confianza del dictamen.\n\n"
            "⚠️ Menos preciso en escaneos torcidos, borrosos, con sellos o manuscritos: puede confundir "
            "caracteres (O↔0, I↔1) y generar más 'Requiere revisión'.",
            icon="🔤",
        )
    else:
        st.warning(
            "**Visión (IA)**\n\n"
            "✅ Lee mejor escaneos difíciles, sellos y tablas.\n\n"
            "⚠️ Las imágenes de las páginas se envían al proveedor del LLM.\n\n"
            "⚠️ Más lento y con costo por página; el resultado puede variar entre corridas.\n\n"
            "⚠️ Un modelo puede 'completar' texto ilegible: la verificación de citas se hace contra "
            "esa lectura, no contra el original. La calidad OCR se fija en 90% (no es medida).\n\n"
            "⚠️ Si la visión falla en una página, usa Tesseract automáticamente.",
            icon="🤖",
        )
    st.caption("Cambiar de motor no reutiliza la caché del otro; la primera corrida con cada motor vuelve a leer los archivos.")
    st.caption(f"LLM: **{prov}**{' · ' + os.getenv('OLLAMA_MODEL', '') if prov == 'ollama' else ''} · OCR: **{motor}** · Umbral de confianza: {cfg()['umbral_confianza']}")
    with st.expander("Diagrama de agentes"):
        mostrar_diagrama()

st.title("📑 Revisión inicial de expedientes inmobiliarios")
st.caption("Recepción → 4 especialistas en paralelo → Validador cruzado → Dictamen con evidencia trazable")

archivos = st.file_uploader("Sube los documentos del expediente (PDF o imagen)", accept_multiple_files=True)

def analizar(rutas: list[str]):
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}
    st.session_state["config"] = config
    with st.status("Agentes trabajando…", expanded=True) as status:
        for evento in grafo().stream({"archivos": rutas, "uso_requerido": uso, "hitl": hitl,
                                      "resultados": [], "bitacora": []}, config, stream_mode="updates"):
            for nodo, upd in evento.items():
                if nodo == "__interrupt__":
                    st.write("👤 En espera de revisión humana")
                    continue
                for linea in (upd or {}).get("bitacora", []):
                    if linea.startswith(("━━", "🏁", "🚩", "🗑️")):
                        st.write(linea)
        status.update(label="Análisis completo", state="complete", expanded=False)


b1, b2 = st.columns([1, 3])
if b1.button("▶️ Analizar expediente", type="primary", disabled=not archivos):
    carpeta = DIR_CACHE / "uploads" / uuid.uuid4().hex[:10]
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for f in archivos:
        ruta = carpeta / Path(f.name).name
        ruta.write_bytes(f.getbuffer())
        rutas.append(str(ruta))
    analizar(rutas)

EJEMPLOS = Path(__file__).parent / "ejemplos"
if EJEMPLOS.exists():
    ej = b2.selectbox("…o usa un expediente sintético de prueba", [""] + sorted(x.name for x in EJEMPLOS.iterdir() if x.is_dir()))
    if ej and b2.button(f"Analizar ejemplo «{ej}»"):
        analizar([str(x) for x in sorted((EJEMPLOS / ej).iterdir()) if x.is_file()])

config = st.session_state.get("config")
if not config:
    st.info("Sube los documentos y presiona **Analizar expediente**. Los archivos pueden venir en cualquier orden y con cualquier nombre: el sistema los clasifica por contenido.")
    st.stop()

snap = grafo().get_state(config)
estado = snap.values
if "dictamen" not in estado:
    st.stop()

d = Dictamen.model_validate(estado["dictamen"])
docs = {x["id"]: Documento.model_validate(x) for x in estado.get("documentos", [])}
resultados = [ResultadoDocumento.model_validate(r) for r in estado.get("resultados_verificados") or estado.get("resultados", [])]
cruces = [Cruce.model_validate(c) for c in estado.get("cruces", [])]

# ------------------------------------------------------------------ encabezado
c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1])
c1.markdown(f"<div style='padding:14px;border-radius:10px;background:{COLOR[d.recomendacion]};color:white'>"
            f"<div style='font-size:14px'>Recomendación inicial</div>"
            f"<div style='font-size:30px;font-weight:700'>{ICONO[d.recomendacion]} {ETIQUETA[d.recomendacion]}</div></div>",
            unsafe_allow_html=True)
c2.metric("Confianza", f"{d.confianza}/100")
c3.metric("Citas verificadas", f"{d.citas_verificadas}/{d.citas_total}")
c4.metric("Discrepancias", len(d.discrepancias))
st.write(d.resumen)

# ------------------------------------------------------------------ human in the loop
if snap.next and "revision_humana" in snap.next:
    with st.container(border=True):
        st.subheader("👤 Revisión humana requerida")
        for p in d.puntos_a_verificar[:15]:
            st.markdown(f"- {p}")
        with st.form("hitl"):
            decision = st.radio("Decisión del revisor", ["cumple", "requiere_revision", "no_cumple"],
                                index=["cumple", "requiere_revision", "no_cumple"].index(d.recomendacion),
                                format_func=lambda k: f"{ICONO[k]} {ETIQUETA[k]}", horizontal=True)
            revisor = st.text_input("Revisor")
            comentario = st.text_area("Comentario")
            if st.form_submit_button("Confirmar decisión"):
                grafo().invoke(Command(resume={"decision": decision, "revisor": revisor, "comentario": comentario}), config)
                st.rerun()
elif estado.get("revision_humana"):
    rh = estado["revision_humana"]
    st.success(f"Decisión humana: {ICONO.get(rh.get('decision'), '')} {ETIQUETA.get(rh.get('decision'), rh.get('decision'))} "
               f"· {rh.get('revisor', '')} · {rh.get('comentario', '')}")

t_res, t_docs, t_datos, t_cruces, t_req, t_bit = st.tabs(
    ["Razones", "Documentos", "Datos extraídos y reglas", "Validaciones cruzadas", "Requisitos", "Bitácora de agentes"])

with t_res:
    for r in d.razones:
        st.markdown(f"- {r}")
    st.markdown("**Señales de confianza (calculadas, no autorreportadas por el LLM)**")
    pesos = cfg()["pesos_confianza"]
    for k, v in d.senales_confianza.items():
        st.progress(min(1.0, v), text=f"{k.replace('_', ' ')} · {v:.0%} (peso {pesos[k]:.0%})")

with t_docs:
    a, b = st.columns(2)
    a.markdown("**Recibidos**")
    for x in d.documentos_recibidos:
        a.markdown(f"- ✅ {x}")
    b.markdown("**Faltantes**")
    for x in d.documentos_faltantes or ["ninguno"]:
        b.markdown(f"- {'⚠️ ' if d.documentos_faltantes else ''}{x}")
    if d.documentos_descartados:
        b.markdown("**Descartados por Recepción**")
        for x in d.documentos_descartados:
            b.markdown(f"- 🗑️ {x}")
    st.dataframe([{"archivo": x.nombre_archivo, "tipo": NOMBRES_TIPO.get(x.tipo, x.tipo), "método": x.tipo_metodo,
                   "conf. clasificación": x.tipo_confianza, "páginas": len(x.paginas),
                   "calidad OCR": round(x.calidad, 2), "grupo (inmueble)": x.grupo} for x in docs.values()],
                 width="stretch")

with t_datos:
    for r in resultados:
        with st.expander(f"{ICONO[r.estado]} {NOMBRES_TIPO[r.tipo]} — {r.nombre_archivo} · {ETIQUETA[r.estado]}"):
            st.caption(f"{r.agente} · obligatorios {r.obligatorios_encontrados}/{r.obligatorios_total} · OCR {r.calidad_ocr:.0%}")
            st.dataframe([{"campo": c.nombre, "valor": c.valor, "pág.": c.evidencia.pagina if c.evidencia else None,
                           "fragmento": c.evidencia.fragmento if c.evidencia else None,
                           "verificada": ("✔" if c.evidencia.verificada else "✖") if c.evidencia else "",
                           "confianza": c.confianza} for c in r.campos if c.valor], width="stretch")
            st.markdown("**Reglas evaluadas**")
            for i, h in enumerate(r.hallazgos):
                icon = "ℹ️" if h.severidad == "info" else ICONO[h.resultado]
                st.markdown(f"{icon} `{h.regla_id}` *({h.severidad})* {h.descripcion}")
                for j, ev in enumerate(h.evidencias):
                    with st.popover(f"evidencia p.{ev.pagina}"):
                        mostrar_evidencia(ev.model_dump(), docs, f"h-{r.documento_id}-{i}-{j}")

with t_cruces:
    if d.discrepancias:
        st.subheader("Inconsistencias (evidencia lado a lado)")
        for i, x in enumerate(d.discrepancias):
            with st.container(border=True):
                st.markdown(f"{'❌' if x.severidad == 'critica' else '⚠️'} **{x.atributo.replace('_', ' ')}** · {x.explicacion}")
                cols = st.columns(max(1, len(x.valores)))
                for col, (did, val) in zip(cols, x.valores.items()):
                    with col:
                        st.markdown(f"**{did}**: «{val}»")
                        ev = next((e.model_dump() for e in x.evidencias if e.documento_id == did), None)
                        mostrar_evidencia(ev, docs, f"d-{i}-{did}")
    st.subheader("Todas las comparaciones")
    st.dataframe([{"atributo": c.atributo, "valores": " | ".join(f"{k}: {v}" for k, v in c.valores.items()),
                   "score": c.score, "resultado": c.resultado, "método": c.metodo, "nota": c.explicacion} for c in cruces],
                 width="stretch")

with t_req:
    a, b = st.columns(2)
    a.markdown("**Cumplidos**")
    for x in d.requisitos_cumplidos:
        a.markdown(f"- ✅ {x}")
    b.markdown("**No cumplidos / en revisión**")
    for x in d.requisitos_no_cumplidos or ["ninguno"]:
        b.markdown(f"- ⚠️ {x}")
    st.markdown("**Puntos a verificar por el equipo legal**")
    for x in d.puntos_a_verificar or ["ninguno"]:
        st.checkbox(x, key=f"pv-{hash(x)}")

with t_bit:
    st.code("\n".join(estado.get("bitacora", [])), language=None)

st.download_button("⬇️ Reporte (Markdown)", markdown(estado), file_name="dictamen.md")
st.download_button("⬇️ Resultado completo (JSON)", json.dumps(estado, ensure_ascii=False, indent=2, default=str),
                   file_name="dictamen.json")
