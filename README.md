# Expedientes 3B · Revisión multiagente (Reto 1 · Hackatón Tiendas 3B)

Sistema multiagente (LangChain + LangGraph) que revisa el expediente legal de un inmueble, detecta faltantes e
inconsistencias, cruza la información entre documentos y emite **Cumple / Requiere revisión / No cumple**,
con evidencia trazable (documento + página + fragmento verificado) en cada hallazgo.

La interfaz está en `frontend/` (Next.js). El grafo vive en `expediente/` y no se reescribe: la API HTTP solo lo llama.

## Arranque de la integración

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Por defecto del ejemplo: LLM_PROVIDER=ollama + OLLAMA_MODEL=qwen2.5:7b
# (ollama pull qwen2.5:7b). Para nube Ollama: LLM_PROVIDER=ollama_cloud + OLLAMA_API_KEY.
# No pongas una clave de Ollama en OPENAI_API_KEY: la API la rechaza a propósito.
uvicorn expediente.api:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```bash
cd frontend
cp .env.example .env.local      # API en http://localhost:8000 y NEXT_PUBLIC_USE_MOCKS=false
npm install
npm run dev
```

La interfaz queda en http://localhost:3000. El análisis pide el uso `tienda` o `cedis` y devuelve el JSON del grafo (`dictamen`, `bitacora`, `resultados_verificados`, `cruces`, `discrepancias`).

Requisitos externos: Tesseract con idioma `spa` (ruta en `TESSERACT_CMD`).

## Prototipo Streamlit y CLI

Siguen disponibles. No sustituyen al grafo.

```bash
streamlit run app.py
python -m expediente.cli analizar ejemplos/problemas --uso tienda
python -m expediente.cli agrupar datos/ --analizar
python -m expediente.cli diagrama
python -m pytest -q tests
```

## Arquitectura

```mermaid
graph TD
  A[Usuario: archivos + uso tienda/CEDIS] --> R[1 · Recepción<br/>OCR · clasificación por contenido · agrupación · faltantes]
  R -- Send --> E[2 · Escrituras]
  R -- Send --> P[3 · Predial]
  R -- Send --> L[4 · Alineamiento y N° oficial]
  R -- Send --> U[5 · Uso de suelo]
  R -. sin documentos .-> V
  E & P & L & U --> V[6 · Validador cruzado<br/>corre SIEMPRE]
  V --> D[1' · Dictamen<br/>verifica citas · confianza calculada]
  D -- Cumple --> F((Fin))
  D -- Revisión / No cumple, si hitl --> H[Revisión humana<br/>interrupt LangGraph] --> F
  T{{Herramientas deterministas @tool<br/>CURP/RFC · direcciones · nombres · superficies<br/>vigencias · verificar_cita · KB}} -.-> E & P & L & U & V & D
```

| Agente | Archivo | Qué hace |
|---|---|---|
| Recepción | [expediente/agents/recepcion.py](expediente/agents/recepcion.py) | Descarta no-documentos y duplicados, OCR, clasifica por contenido (palabras clave del YAML + LLM), extrae huella y agrupa por inmueble |
| Especialistas ×4 | [expediente/agents/especialistas.py](expediente/agents/especialistas.py) | Extracción estructurada `{valor, página, fragmento}`, reglas del YAML, consulta de KB, estado de 3 valores + motivos |
| Validador cruzado | [expediente/agents/validador.py](expediente/agents/validador.py) | Dirección, número oficial, propietario (escritura↔predial), superficie, clave catastral, documentos de otro inmueble |
| Dictamen | [expediente/agents/dictamen.py](expediente/agents/dictamen.py) | Verifica cada cita contra el OCR, calcula confianza, aplica reglas de dictamen. El cierre, no un séptimo agente de la lista |

La API llama `ejecutar()` con `hitl=False`, igual que la CLI. Si el dictamen no es Cumple, la respuesta trae `requiere_humano` y `puntos_a_verificar`. El interrupt de LangGraph queda apagado.

### Decisiones clave
- **Reglas en configuración, no en prompts**: [config/reglas/*.yaml](config/reglas/) (campos, reglas críticas/menores, vigencias) y [config/dictamen.yaml](config/dictamen.yaml) (umbral, pesos, usos compatibles, tolerancias). Cambiar a las reglas oficiales no toca código.
- **Nada se corta antes de tiempo**: si falta un documento o un especialista falla, el resultado es *Requiere revisión* y el validador cruzado corre igual.
- **No cumple solo con evidencia clara y verificada**: uso de suelo incompatible por palabras clave, o documento de otro inmueble con ≥2 señales independientes. Un juicio del LLM nunca rechaza por sí solo; un incumplimiento cuya cita no se verifica baja a *Requiere revisión*.
- **Anti-alucinación**: cada fragmento citado se busca en el texto OCR (fuzzy ≥ 85, todas las páginas si la página citada no cuadra).
- **Confianza calculada**: calidad OCR, % campos obligatorios, % reglas que pasan, score de cruces y % de citas verificadas (pesos en YAML). Con faltantes nunca supera el umbral.
- **CURP/RFC**: formato + dígito verificador; corrige confusiones típicas del OCR (O↔0, I↔1…) y lo deja anotado.
- **Predial a nombre de otra persona** = discrepancia menor (*Requiere revisión*), no rechazo.
- **KB por especialista** ([kb/](kb/)): contexto, no prueba de autenticidad. Altas automáticas quedan como *Pendientes* y se guardan sin datos personales.

## Motor OCR (elegible)
Selector en la barra lateral de Streamlit, `--ocr tesseract|vision` en la CLI, o `OCR_MOTOR=` en `.env`.

| | Tesseract (sin IA, por defecto) | Visión (IA) |
|---|---|---|
| Dónde corre | Local | Imágenes de páginas al proveedor del LLM |
| Costo / velocidad | Gratis, rápido | Costo por página, más lento |
| Calidad | Confianza real por palabra; falla en escaneos malos (O↔0, I↔1) | Mejor en escaneos difíciles; puede "completar" texto ilegible |
| Calidad OCR reportada | Medida | Fija en 90% (no medida) |
| Si falla | — | Cae a Tesseract por página |

La caché por hash distingue el motor.

Uso: `python -m expediente.cli agrupar archivos_prueba --ocr vision`
