"""Analiza con reglas el OCR de todos los documentos y arma el catálogo de expedientes.
   - analisis/<grupo>-<tipo>.json  (mismo formato que el resto: páginas, pasos con caja de evidencia, confianza)
   - analisis/expedientes.json     (un expediente por predio, con los documentos que ya tenemos; los que faltan quedan vacíos)
   - analisis/indice.json          (para reconocer un PDF subido por nombre y tamaño)
Los datos leídos con poca confianza (OCR < 0.80) o ausentes quedan marcados «para revisión humana».
Uso: python3 -I herramientas/analizar_todos.py <carpeta_ocr_todos>"""
import json, os, re, shutil, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR = sys.argv[1]
MAN = {m['k']: m for m in json.load(open(f'{OCR}/manifest.json'))}

# ---- expedientes: grupo -> datos y documentos (clave del manifiesto) -------------------------------------------------
# busqueda = texto para ubicar el predio en el mapa; None = documento sintético o sin dirección ubicable
EXPS = [
 dict(id='tepeji5', nombre='Tepeji del Río 5 · Av. Melchor Ocampo, Col. Atengo', muni='Tepeji del Río de Ocampo, Hidalgo', busqueda='Avenida Melchor Ocampo, Barrio de Atengo, Tepeji del Río de Ocampo, Hidalgo', docs=dict(escrituras='d28', predial='d35', alineamiento='d07', uso='d58'), curado=True),
 dict(id='mirador', nombre='El Mirador, Ocotlán de las Torres (sintético)', muni='Ocotlán de las Torres, Estado de México', busqueda=None, sintetico=True, docs=dict(escrituras='d18', predial='d30', alineamiento='d01', uso='d46')),
 dict(id='laloma', nombre='La Loma, San Jerónimo Atlaco (sintético)', muni='San Jerónimo Atlaco, Estado de México', busqueda=None, sintetico=True, docs=dict(escrituras='d20', predial='d32', alineamiento='d03', uso='d48')),
 dict(id='fresnos', nombre='Villa de los Fresnos, Huehuetlán del Monte (sintético)', muni='Huehuetlán del Monte', busqueda=None, sintetico=True, docs=dict(escrituras='d21', predial='d33', alineamiento='d04', uso='d49')),
 dict(id='sanantonio', nombre='Barrio San Antonio · escaneo desvanecido (sintético)', muni='Barrio San Antonio', busqueda=None, sintetico=True, docs=dict(escrituras='d19', predial='d31', alineamiento='d02', uso='d47')),
 dict(id='sorjuana', nombre='Sor Juana · Ricardo Flores Magón, Tepotzotlán', muni='Tepotzotlán, Estado de México', busqueda='Calle Ricardo Flores Magón, Tepotzotlán, Estado de México', docs=dict(escrituras='d24', predial='d34', alineamiento='d06', uso='d51'), extras=[('alineamiento', 'd05')]),
 dict(id='melchorocampo3', nombre='Melchor Ocampo III · Av. Crispín Pérez 174', muni='Melchor Ocampo, Estado de México', busqueda='Avenida Crispín Pérez 174, Centro, Melchor Ocampo, Estado de México', docs=dict(escrituras='d23', predial='d29', alineamiento='d00', uso='d50')),
 dict(id='crispin', nombre='Melchor Ocampo · Av. Crispín Pérez S/N (licencia 2009)', muni='Melchor Ocampo, Estado de México', busqueda='Avenida Crispín Pérez, Melchor Ocampo, Estado de México', docs=dict(uso='d53')),
 dict(id='tultepec-insurgentes', nombre='Tultepec · Insurgentes, Santa Rita', muni='Tultepec, Estado de México', busqueda='Avenida Insurgentes, Santa Rita, Tultepec, Estado de México', docs=dict(predial='d39', alineamiento='d14', uso='d61')),
 dict(id='tultepec-sanjuan', nombre='Tultepec · San Juan', muni='Tultepec, Estado de México', busqueda='San Juan, Tultepec, Estado de México', docs=dict(predial='d45', alineamiento='d15')),
 dict(id='quma-pedregal', nombre='Quma · Sendero del Pedregal Sur', muni='Atotonilco de Tula, Hidalgo', busqueda='Boulevard Sendero del Pedregal Sur, Atotonilco de Tula, Hidalgo', docs=dict(escrituras='d26', alineamiento='d13')),
 dict(id='toscana', nombre='La Toscana · Praderas del Potrero, Atotonilco de Tula', muni='Atotonilco de Tula, Hidalgo', busqueda='Fraccionamiento La Toscana, Atotonilco de Tula, Hidalgo', docs=dict(escrituras='d25', predial='d36', uso='d60')),
 dict(id='tlahuelilpan', nombre='Tlahuelilpan · 16 de Enero de 1869, Col. Cuauhtémoc', muni='Tlahuelilpan, Hidalgo', busqueda='Calle 16 de Enero de 1869, Colonia Cuauhtémoc, Tlahuelilpan, Hidalgo', docs=dict(escrituras='d22', predial='d37', alineamiento='d09', uso='d57')),
 dict(id='mixquiahuala', nombre='Mixquiahuala · Blvd. Octaviano Flores Mayorga', muni='Mixquiahuala de Juárez, Hidalgo', busqueda='Boulevard Octaviano Flores Mayorga 36, Mixquiahuala de Juárez, Hidalgo', docs=dict(predial='d41', alineamiento='d08', uso='d52')),
 dict(id='tezontepec', nombre='Tezontepec de Aldama · San Bernardino, El Tinaco', muni='Tezontepec de Aldama, Hidalgo', busqueda='Carretera Tula-Actopan Km 27.5, El Tinaco, Tezontepec de Aldama, Hidalgo', docs=dict(predial='d44', alineamiento='d12', uso='d56')),
 dict(id='ixmiquilpan', nombre='Ixmiquilpan · Lázaro Cárdenas, Barrio San Miguel', muni='Ixmiquilpan, Hidalgo', busqueda='Calle Lázaro Cárdenas, Barrio San Miguel, Ixmiquilpan, Hidalgo', docs=dict(escrituras='d27', predial='d38', alineamiento='d17')),
 dict(id='temascalcingo', nombre='Temascalcingo · Calzada del Molino', muni='Temascalcingo, Estado de México', busqueda='Calzada del Molino, Centro, Temascalcingo, Estado de México', docs=dict(alineamiento='d10', uso='d54')),
 dict(id='villadelcarbon', nombre='Villa del Carbón · Alfredo del Mazo S/N', muni='Villa del Carbón, Estado de México', busqueda='Avenida Alfredo del Mazo, Villa del Carbón, Estado de México', docs=dict(predial='d40', alineamiento='d16', uso='d59')),
 dict(id='cassidy', nombre='Villa del Carbón · Cassidy Barrios', muni='Villa del Carbón, Estado de México', busqueda='Villa del Carbón, Estado de México', docs=dict(alineamiento='d11', uso='d55')),
 dict(id='lomaalta', nombre='Villa del Carbón · La Manzana, Loma Alta', muni='Villa del Carbón, Estado de México', busqueda='Loma Alta, Villa del Carbón, Estado de México', docs=dict(predial='d43')),
 dict(id='xhala', nombre='San Sebastián Xhala', muni='San Sebastián Xhala, Estado de México', busqueda='San Sebastián Xhala, Estado de México', docs=dict(predial='d42')),
]
# análisis que ya existían (documentos sintéticos de la demostración)
YA = {'d18': '01-escritura-2', 'd19': '01-escritura', 'd20': '01-escritura-1', 'd21': '01-escriturav'}
# análisis curados a mano (Tepeji 5)
CURADO = {'d28': 'tepeji5-escritura', 'd35': 'tepeji5-predial', 'd07': 'tepeji5-alineamiento', 'd58': 'tepeji5-uso'}

TITULOS = {'escrituras': 'Escritura', 'predial': 'Predial', 'alineamiento': 'Alineamiento y número oficial', 'uso': 'Uso de suelo'}
MESES = 'enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre'
N = r"((?:[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ\.]*\s+){1,5}[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ\.]*)"      # nombre propio (2 a 6 palabras)

def cargar(k): return json.load(open(f'{OCR}/{k}/ocr.json'))

def textos(P):
    out = []
    for p in P:
        partes, spans, pos = [], [], 0
        for l in p['lineas']:
            spans.append((pos, pos + len(l['t']), l)); partes.append(l['t']); pos += len(l['t']) + 1
        out.append((' '.join(partes), spans))
    return out

def buscar(TX, rx, grupo=1, flags=0, desde=0):
    for pi, (T, spans) in enumerate(TX):
        if pi < desde: continue
        m = re.search(rx, T, flags)
        if not m or not m.group(grupo): continue
        a, b = m.span(grupo)
        ls = [l for s, e, l in spans if s < b and e > a]
        if not ls: continue
        x0 = min(l['x'] for l in ls); y0 = min(l['y'] for l in ls); x1 = max(l['x'] + l['w'] for l in ls); y1 = max(l['y'] + l['h'] for l in ls)
        pad = 0.004; x0, y0 = max(0, x0 - pad), max(0, y0 - pad); x1, y1 = min(1, x1 + pad), min(1, y1 + pad)
        return dict(v=re.sub(r'\s+', ' ', m.group(grupo)).strip(' .,;:-_"\''), pagina=pi + 1, rect=[round(x0, 4), round(y0, 4), round(x1 - x0, 4), round(y1 - y0, 4)],
                    conf=round(sum(l['c'] for l in ls) / len(ls), 2))
    return None

def primero_si(TX, valida, rxs, **kw):
    for rx in rxs:
        r = buscar(TX, rx, **kw)
        if r and len(r['v']) >= 3 and valida.search(r['v']): return r
    return None

def primero(TX, rxs, **kw):
    for rx in rxs:
        r = buscar(TX, rx, **kw)
        if r and len(r['v']) >= 3: return r
    return None

ALTO = re.compile(r'\b(?:R[eé]gimen|Domicilio|Dir|PRESENTE|SE|NACIDO|NOM|NOMBRE|En|IDENTIF\w*|Colonia|Col|CENTRO|RFC|CURP|CON|QUE|PARA|UBICAD\w*|CLAVE|CUENTA|MUNICIPIO|ESTADO|HIDALGO|LOCALIDAD|FOLIO|CALLE|AVENIDA|Esta|DATOS|LIQUIDACI\w+|SubTotal|PROPIETARIO|SOLICITANTE|FECHA)\b.*$', re.I)
MALO = re.compile(r'^(?:DE QUIEN|JUEZ|PREDIO|P\. ARCHIVO|ARCHIVO|QUNA|C\.P|AV\.|F\.D\.I|V\.|FOLIO|CENTRO|ARCHIVO|ESTADO|MUNICIPIO|DIRECCI|SECRETAR|H\. |TESORER|GOBIERNO|PRESIDENCIA|ARQ|LIC|ING|DIRECTOR|NOTAR|REPRESENTANTE)', re.I)
def nombre(v):
    v = re.sub(r'^(?:O )?C\. ?', '', v.strip()); v = re.sub(r'^(?:DE|DEL|LA|EL) ', '', v); v = ALTO.sub('', v).strip(' .,;:-/'); v = re.sub(r' (?:DE|DEL|LA|Y|DE LA)$', '', v)
    if len(v.split()) < 2 or re.search(r'\d', v) or MALO.match(v): return None
    return v

def extraer(tipo, P):
    TX = textos(P); pasos = []
    def add(campo, r, nota=None, fmt=None, falta_nota=None, obligatorio=False):
        if r is None:
            if obligatorio: pasos.append(dict(campo=campo, valor='No legible', pagina=1, rect=[0.08, 0.1, 0.84, 0.05], ok=False, confianza=0.0,
                nota=falta_nota or 'Sin lectura automática: no se encontró el dato en el texto reconocido. Verificar en el documento original.'))
            return
        v = fmt(r['v']) if fmt else r['v']
        ok = r['conf'] >= 0.80
        n = nota if ok else ((nota + ' ' if nota else '') + 'Lectura de baja confianza: verificar contra el original.')
        d = dict(campo=campo, valor=v[:150], pagina=r['pagina'], rect=r['rect'], ok=ok, confianza=r['conf'])
        if n: d['nota'] = n
        pasos.append(d)
    # tipo documental y autoridad
    pasos.append(dict(campo='Tipo documental', valor={'escrituras': 'Escritura pública', 'predial': 'Predial', 'alineamiento': 'Constancia de alineamiento y número oficial', 'uso': 'Uso de suelo'}[tipo],
                      pagina=1, rect=[0.06, 0.02, 0.88, 0.12], ok=True, confianza=1.0))
    add('Autoridad emisora', primero(TX, [r'((?:H\. )?AYUNTAMIENTO[^|]{0,50})', r'((?:SECRETAR[IÍ]A|TESORER[IÍ]A|DIRECCI[OÓ]N)[^|]{4,60})', r'(NOTAR[IÍ]A [^|]{3,40})'], flags=re.I), fmt=lambda s: s[:80])
    add('Fecha de expedición', primero(TX, [rf'(\d{{1,2}}\s+de\s+(?:{MESES})\s+(?:de|del)\s+\d{{4}})', rf'((?:{MESES})\s+\d{{1,2}},?\s+\d{{4}})'], flags=re.I))
    # titular
    anclas = ([rf'(?i:(?:LA PARTE COMPRADORA|COMPRADOR|adquirente|donataria?|donatario)[^.]{{0,60}}?(?:se[ñn]or(?:a)?|C\.)\s*){N}', rf'(?i:a favor de (?:la |el )?(?:se[ñn]or(?:a)? |C\. )?){N}']
              if tipo == 'escrituras' else []) + [rf'(?i:NOMBRE DEL PROPIETARIO\s*[:.]?\s*){N}', rf'(?i:PROPIETARIO(?: / POSEEDOR)?\s*[:.]?\s+){N}', rf'(?i:a favor (?:de la|de el|del|de)\s+(?:C\.\s*)?){N}',
              rf'(?i:solicit\w+[^.]{{0,40}}?C\.\s*){N}', rf'(?i:\bC\.\s*){N}', rf'(?i:\bNOMBRE\s*[:.]?\s+){N}', rf'(?i:contribuyente\s*[:.]?\s*){N}', rf'(?i:se[ñn]or(?:a)?\s+){N}']
    r = None
    for rx in anclas:
        c = buscar(TX, rx)
        if c and nombre(c['v']): c['v'] = nombre(c['v']); r = c; break
    add('Titular actual', r, obligatorio=True)
    DIR_OK = re.compile(r'\b(calle|av\.?|avenida|boulevard|carretera|km|colonia|col\.|barrio|lote|calzada|sin n[uú]mero|s/n|sn|fracc\w*|ejido|comunidad|privada|cerrada|camino|manzana)\b', re.I)
    LIMPIA = lambda v: re.sub(r' (?:SubTotal|Recargo|Clave|CLAVE|Total)\b.*$', '', v)
    add('Dirección del inmueble', primero_si(TX, DIR_OK, [r'(?i:ubicad[oa]s?\s+(?:actualmente\s+)?en\s+)(.{10,150}?)(?:(?<=[A-Za-zÁÉÍÓÚáéíóúñ]{4})\.|;| (?:perteneciente|de acuerdo|el cual|con una|y que)\b)', r'(?i:ubicaci[oó]n en\s+)(.{10,150}?)(?:(?<=[A-Za-zÁÉÍÓÚáéíóúñ]{4})\.| CLAVE)',
                                               r'(?i:(?:DOMICILIO|UBICACI[OÓ]N(?: DEL PREDIO)?)\s*[:.]?\s+)((?:Av|AV|Calle|CALLE|Boulevard|Carretera|CARRETERA|Priv|Cerrada|Camino)[^|]{6,110}?)(?= LOCALIDAD| CLAVE| SUPERFICIE| DATOS| COL\.? [A-Z]{3,}\b.*(?:CLAVE|SUPERFICIE)|$)',
                                               r'(?i:(?:DOMICILIO|UBICACI[OÓ]N(?: DEL PREDIO)?)\s*[:.]\s*)(.{8,120}?)(?: CLAVE| SUPERFICIE| DATOS|$|\.)',
                                               r'(?i:direcci[oó]n del predio\s*[:.]?\s*)(.{8,120}?)(?: MUNICIPIO|$)', r'(?i:Calle\s*[:.]\s*)(.{6,80}?)(?: Localidad| Municipio|$)']), obligatorio=tipo != 'predial', fmt=LIMPIA)
    add('Superficie del predio', primero(TX, [r'(?i:superficie\s+(?:total\s+)?(?:del\s+)?(?:predio|terreno)[^0-9]{0,40})((?:\d{1,3}(?:[,.]\d{3})+|\d+)(?:\.\d{1,2})?)\s*(?:m2|m²|M2|mts|metros|m\b)?', r'\bSUP\.?\s*((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)\s*(?:m2|m²|M2)', r'(?i:superficie[^0-9]{0,60}?)((?:\d{1,3}(?:[,.]\d{3})+|\d+)(?:\.\d{1,2})?)\s*(?:m2|m²|M2|mts|metros)', r'(\d{1,3}(?:,\d{3})*\.\d{2})\s*(?:m2|m²|M2)']),
        fmt=lambda s: s.replace(',', '') + ' m²', obligatorio=tipo == 'escrituras')
    add('Clave catastral', primero(TX, [r'(?i:clave\s+catastral[^0-9]{0,10})(\d[\d \-]{8,24}\d)', r'\b(\d{3}[ -]\d{2}[ -]\d{3}[ -]\d{2}[ -]\d{2}[ -]?\d{3,4})\b', r'\b(\d{16})\b']), fmt=lambda s: re.sub(r'\s+', ' ', s))
    add('Identificación del predio', primero(TX, [r'(?i:Lote\s*[:.]?\s*)(\w{1,4}[^|]{0,30}?Manzana\s*[:.]?\s*\w{1,4})', r'(?i:Lote\s*[:.]?\s*)(\w{1,4}\s*,?\s*(?:Mz\.?|Manz\.?)\s*:?\s*\w{1,4})', r'(?i:denominado\s+)(["“][^"”]{3,40}["”])']),
        fmt=lambda s: ('Lote ' + s) if re.match(r'^\w{1,4}\b', s) and 'denomin' not in s.lower() and not s.startswith('"') and not s.startswith('“') else s)
    if tipo == 'alineamiento':
        r = primero(TX, [r'(?i:corresponde el N[uú]mero Oficial\s+)(\d{1,5})\b', r'(?i:n[uú]mero oficial\s*(?:asignado|autorizado)?\s*[:.]?\s*(?:es\s+)?)(\d{1,5}|S/N)\b', r'(?i:Num\.? Oficial\s*[:.]?\s*)(\d{1,5}|S/N)\b'])
        if r is None:                                   # si no viene aparte, sale de la dirección («No. 120» o «S/N»)
            r = primero(TX, [r'(?i:(?:ubicad[oa]s?\s+(?:actualmente\s+)?en|ubicaci[oó]n en)\s+[^|]{0,80}?\b(?:No\.?|N[uú]m\.?|n[uú]mero)\s*)(\d{1,5}|S/N)\b'])
            if r: r['conf'] = min(r['conf'], 0.9)
        add('Número oficial', r, obligatorio=True)
        add('Vigencia', primero(TX, [r'(?i:(?:vigencia|v[aá]lid[ao]|vigente)[^.]{0,80}?)((?:seis|6|doce|12|dos|2|tres|3)\s*(?:meses|a[ñn]os|d[ií]as)[^.]{0,40})', r'(?i)(\b(?:un|1)\s+a[ñn]o\b[^.]{0,30})']), nota='Verificar contra la fecha de expedición.')
    if tipo == 'uso':
        add('Uso de suelo', primero(TX, [r'(?i:uso\s+(?:de\s+)?suelo[^.]{0,40}?(?:autoriza|autorizado|exclusivo|compatible|permitido)[^.]{0,20}?)(["“]?\s*(?:comercial|habitacional|mixto|industrial|servicios)[^.]{0,60})',
                                          r'(?i)((?:zona|uso)[^.]{0,20}(?:habitacional|comercial|mixto|industrial)[^.]{0,60})']), obligatorio=True)
        add('Vigencia', primero(TX, [r'(?i:(?:vigencia|v[aá]lid[ao]|vigente)[^.]{0,80}?)((?:seis|6|doce|12|dos|2|tres|3|180)\s*(?:meses|a[ñn]os|d[ií]as)[^.]{0,40})', r'(?i)(\b(?:un|1)\s+a[ñn]o\b[^.]{0,30})']), nota='Verificar contra la fecha de expedición.')
    if tipo == 'predial':
        add('Cuenta predial', primero(TX, [r'(?i:cuenta[^A-Z0-9]{0,12})(U[- ]?\d{4,6})', r'\b(U-?\d{5,6})\b']))
        add('Valor catastral', primero(TX, [r'(?i:valor\s+(?:catastral|fiscal)\s*[:.]?\s*)(\$?\s*[\d,]+\.?\d*)']))
    if tipo == 'escrituras':
        add('Instrumento y volumen', primero(TX, [r'(?i:(?:escritura|instrumento)\s+(?:n[uú]mero\s+)?)(\d[\d,\.]*)(?:[^|]{0,60}?volumen\s+(\d[\d,\.]*))?']), fmt=lambda s: 'Instrumento ' + s)
        add('Precio de la operación', primero(TX, [r'(?i:precio[^$]{0,80}?)(\$\s*[\d,]+\.\d{2})']))
    pasos.sort(key=lambda d: (d['pagina'], d['rect'][1]))
    for i, d in enumerate(pasos, 1): d.update(agente='Extractor', n=i, t='00:%04.1f' % (0.7 * i)); d.setdefault('nota', '')
    return pasos

indice_path = f'{RAIZ}/analisis/indice.json'
indice = {e['id']: e for e in json.load(open(indice_path))}
usados = {}
def procesar(k, id_, grupo, tipo):
    m = MAN[k]; P = cargar(k)
    if id_ not in CURADO.values() and id_ not in YA.values():
        out_pg = f'{RAIZ}/paginas/{id_}'; os.makedirs(out_pg, exist_ok=True)
        for p in P: shutil.copy(f'{OCR}/{k}/p{p["pagina"]}.jpg', f'{out_pg}/p{p["pagina"]}.jpg')
        pasos = extraer(tipo, P)
        an = dict(id=id_, tipo=tipo, grupo=grupo, archivo=m['archivo'], titulo=f'{TITULOS[tipo]} · {grupo}', parcial=len(P) < 99,
                  paginas=[dict(n=p['pagina'], img=f'paginas/{id_}/p{p["pagina"]}.jpg', w=p['w'], h=p['h']) for p in P], total_paginas=len(P), pasos=pasos,
                  resumen=dict(validados=sum(1 for d in pasos if d['ok']), revisar=sum(1 for d in pasos if not d['ok'])))
        json.dump(an, open(f'{RAIZ}/analisis/{id_}.json', 'w'), ensure_ascii=False, indent=1)
        indice[id_] = dict(id=id_, tipo=tipo, grupo=grupo, archivo=m['archivo'], originales=[m['archivo']], bytes=m['bytes'], titulo=an['titulo'], paginas=len(P), pasos=len(pasos), revisar=sum(1 for d in pasos if not d['ok']))
    else:
        indice[id_].update(tipo=tipo, grupo=grupo)
        if id_ in YA.values(): indice[id_]['bytes'] = m['bytes']; indice[id_]['originales'] = sorted(set(indice[id_].get('originales', []) + [m['archivo']]))

exps = []
for e in EXPS:
    docs = {}
    for tipo, k in e['docs'].items():
        id_ = CURADO.get(k) or YA.get(k) or f"{e['id']}-{tipo}"
        procesar(k, id_, e['id'], tipo); docs[tipo] = id_
    extras = []
    for tipo, k in e.get('extras', []):
        id_ = f"{e['id']}-{tipo}-2"; procesar(k, id_, e['id'], tipo); extras.append(id_)
    exps.append(dict(id=e['id'], nombre=e['nombre'], municipio=e['muni'], busqueda=e['busqueda'], coords=None, sintetico=bool(e.get('sintetico')), docs=docs, extras=extras))
json.dump(exps, open(f'{RAIZ}/analisis/expedientes.json', 'w'), ensure_ascii=False, indent=1)
json.dump(list(indice.values()), open(indice_path, 'w'), ensure_ascii=False, indent=1)
n = sum(len(e['docs']) + len(e['extras']) for e in exps)
print(len(exps), 'expedientes', n, 'documentos asignados de', len(MAN))
