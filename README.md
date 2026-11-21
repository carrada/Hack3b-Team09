# Tiendas 3B · Mapa de expedientes

Prototipo para revisar expedientes inmobiliarios (escritura, predial, alineamiento y número oficial, uso de suelo) sobre un mapa. Es HTML y JavaScript estático, sin paso de compilación.

**Video de demostración:** [`video`](video.md) (3 min 16 s).

## Qué hace

- **Mapa 3D de Mapbox** con las 62 tiendas, 3 centros de distribución propuestos (con líneas a las tiendas que abastecen) y 21 zonas en estudio. La primera vez que se abre, arranca en la vista del mundo con el logo de 3B y a los 2 segundos vuela a la vista cercana; las siguientes veces abre directo en la vista cercana (`?intro=1` la repite).
- **Panel con tres listas:** Zonas, Tiendas y Centros. Al abrir una zona, tienda o centro, la cámara hace zoom y el panel muestra qué hacer primero, los datos clave (titular, dirección, superficie, número oficial, clave catastral) y los documentos.
- **Investigación en lote:** se eligen varias zonas (con casilla o tocando el mapa), se analizan juntas aunque falten documentos y solo las que tienen detalles pasan a verificación humana.
- **Analizador:** muestra el documento con el texto que sustenta cada hallazgo, qué dice cada documento, el fundamento (regla) y el siguiente paso sugerido.
- **Validación cruzada:** compara los mismos datos entre los cuatro documentos y marca cuáles coinciden, cuáles difieren y cuáles no se pueden contrastar.
- **Revisión por agentes:** reproduce paso a paso qué zona del documento lee cada agente.

## Cómo correrlo

1. Pon tu token público de Mapbox en `index.html`, en la línea `mapboxgl.accessToken = 'PON_AQUI_TU_TOKEN_DE_MAPBOX';`. Sin token el mapa no carga.
2. Desde esta carpeta:

   ```bash
   python3 -m http.server 8000
   ```

3. Abre <http://localhost:8000>.

## Pruebas

```bash
python3 pruebas/datos.py     # datos y modelo, no necesita servidor
python3 pruebas/e2e.py       # navegador sin ventana (WebKit): necesita el servidor en marcha y macOS con Swift
python3 pruebas/e2e.py --solo "mapa ·"
```

Las pruebas del mapa 3D que miden cuadros por segundo fallan a veces en el navegador sin ventana; suelen pasar al repetirlas.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `index.html` | Mapa, panel de listas, investigación en lote y panel de zona |
| `analizador.html`, `validacion.html`, `revision.html` | Pantallas de análisis |
| `modulo.js` | Estado compartido, reglas del expediente y cruce de datos |
| `tiendas.js` | Datos de las 62 tiendas |
| `paginas.css`, `tema.css` | Estilos compartidos; `tema.css` define el tema sobrio de todas las vistas |
| `analisis/` | Un JSON por documento analizado, `expedientes.json` (21 expedientes) e `indice.json` |
| `modelos/` | Modelos 3D (`tienda.glb`, `cedis.glb`) |
| `herramientas/` | OCR (macOS Vision), extractor automático y conversor FBX a GLB |
| `pruebas/` | Pruebas de datos y de extremo a extremo |
| `demo/` | Video de demostración |

## Datos y límites

- Los documentos son reales: 62 archivos agrupados en 21 expedientes, con documentos faltantes cuando no hay los cuatro. Cuatro conjuntos están marcados «HACKATHON 3B» y son sintéticos, por eso aparecen «sin ubicación».
- **Solo Tepeji del Río 5 se verificó a mano** contra las imágenes. En los demás, los datos salen del extractor automático (`herramientas/analizar_todos.py`) y los que tienen baja confianza quedan marcados para revisión humana.
- Los análisis ya están calculados. **No hay un backend que analice PDFs nuevos**, y la interfaz no muestra un nivel de confianza numérico: muestra la recomendación y sus motivos.
- Las imágenes de las páginas (`paginas/`) y los PDF originales no están en el repositorio por su tamaño; sin ellas el analizador no puede mostrar los documentos.
- Los 3 centros de distribución son ubicaciones propuestas por agrupación de tiendas, no direcciones reales.
- Las ubicaciones de las zonas se obtienen con el geocodificador de Mapbox y quedan guardadas en el navegador; varias son aproximadas.

## Diseño

Tema sobrio basado en el criterio del [GOV.UK Design System](https://design-system.service.gov.uk/) (`alphagov/govuk-frontend`, licencia MIT): estados dichos con palabras, listas de resumen, avisos sin cajas de color, enlaces subrayados y una sola tipografía (IBM Plex Sans). El rojo de la marca se usa en la barra lateral, el logo y la acción principal.
