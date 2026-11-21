"""Genera analisis/<id>.json y paginas/<id>/pN.jpg de los 4 documentos reales del expediente Tepeji del Río 5
a partir del OCR (herramientas/ocr_pdf.swift). Cada dato lleva su caja de evidencia tomada de las líneas reconocidas.
Los valores se verificaron a mano contra las imágenes de los PDFs.   Uso: python3 -I herramientas/crear_analisis.py <carpeta_ocr>"""
import json, os, re, shutil, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR = sys.argv[1]
DOCS = '/Users/kombo/Documents/hack3b/docs_prueba'
GRUPO = 'tepeji5'

def cargar(k): return json.load(open(f'{OCR}/{k}/ocr.json'))

def caja(paginas, pag, patrones, pad=0.004):
    """unión de las líneas de la página `pag` que casan con alguno de los patrones; devuelve ([x,y,w,h], confianza)"""
    ls = [l for l in paginas[pag - 1]['lineas'] if any(re.search(p, l['t'], re.I) for p in patrones)]
    assert ls, f'sin coincidencias en p{pag}: {patrones}'
    x0 = min(l['x'] for l in ls); y0 = min(l['y'] for l in ls); x1 = max(l['x'] + l['w'] for l in ls); y1 = max(l['y'] + l['h'] for l in ls)
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(1, x1 + pad), min(1, y1 + pad)
    return [round(x0, 4), round(y0, 4), round(x1 - x0, 4), round(y1 - y0, 4)], round(sum(l['c'] for l in ls) / len(ls), 2)

# (agente, campo, valor, página, [patrones], ok, nota)
ESC = [
 ('Extractor', 'Tipo documental', 'Escritura pública · Contrato de compraventa', 2, [r'COMPRAVENTA que otorgan', r'^COMPRAVENTA|COMPRAVENTA que'], True, None),
 ('Extractor', 'Autoridad emisora', 'Notaría Pública No. 101 · Estado de México', 1, [r'NOTARIA 101'], True, None),
 ('Extractor', 'Instrumento y volumen', 'Escritura número 33,239 · Volumen 499', 2, [r'ESCRITURA NÚMERO TREINTA', r'VOLUMEN CUATROCIENTOS'], True, None),
 ('Extractor', 'Fecha de otorgamiento', '6 de marzo de 2025', 2, [r'En Jilotepec, Estado de México a los seis'], True, None),
 ('Extractor', 'Transmitente (vendedor)', 'Regalos Ultramar, S.A. de C.V.', 2, [r'REGALOS', r'ULTRAMAR'], True, None),
 ('Extractor', 'Adquirente (comprador)', 'José Haber Douek', 2, [r'PARTE COMPRADORA" el señor JOSÉ HABER'], True, None),
 ('Extractor', 'Titular actual', 'José Haber Douek', 2, [r'PARTE COMPRADORA" el señor JOSÉ HABER'], True, 'El comprador pasa a ser el titular del predio al firmarse la escritura.'),
 ('Extractor', 'Dirección del inmueble', 'Predio urbano «El Paso del Norte», Barrio de Atengo, Tepeji del Río de Ocampo, Hidalgo', 2,
   [r'adquirió la propiedad del predio urbano', r'de Atengo, Municipio de Tepeji', r'él existentes, con la superficie'], False,
   'La escritura describe el predio por su nombre y barrio, sin calle ni número oficial. El anexo catastral lo ubica en Av. Melchor Ocampo S/N, Colonia Atengo.'),
 ('Extractor', 'Número oficial', 'S/N', 18, [r'UBICACIÓN: AV. MELCHOR OCAMPO S/N', r'^HIDALGO\.'], True, 'Según la constancia catastral anexa a la escritura (pág. 18).'),
 ('Extractor', 'Identificación del predio', 'El Paso del Norte, Barrio de Atengo', 2, [r'adquirió la propiedad del predio urbano', r'de Atengo, Municipio de Tepeji'], True, None),
 ('Extractor', 'Superficie del predio', '890.00 m²', 2, [r'CON UNA SUPERFICIE APROXIMADA', r'DE 890\.00 METROS'], True, 'La escritura la declara «aproximada»; coincide con el certificado del Registro y la constancia catastral anexos.'),
 ('Extractor', 'Clave catastral', '63 01 144 006', 3, [r'la clave catastral número', r'tres cero uno uno cuatro cuatro cero cero seis'], True, None),
 ('Extractor', 'Cuenta predial', 'U0003410', 3, [r'bajo el número de cuenta'], True, None),
 ('Extractor', 'Libertad de gravamen', 'Libre de gravámenes · certificado del 13 de febrero de 2025', 16, [r'NO REPORTA GRAVAMEN'], True,
   'El certificado del Registro Público (Tula de Allende) va en el apéndice: «No reporta gravamen». Tenía 21 días de antigüedad al firmarse.'),
 ('Extractor', 'Precio de la operación', '$6,900,000.00', 4, [r'es la cantidad de \$6,900,000\.00', r'PESOS 00/100 MONEDA NACIONAL\) que'], True, None),
]
PRE = [
 ('Extractor', 'Tipo documental', 'Recibo de pago del impuesto predial 2025', 1, [r'PAGO DE IMPUESTO PREDIAL'], True, None),
 ('Extractor', 'Autoridad emisora', 'Municipio de Tepeji del Río de Ocampo, Hidalgo', 1, [r'MPIO TEPEJI DEL RIO'], True, None),
 ('Extractor', 'Folio y fecha de pago', 'Folio 25014300 · 28 de enero de 2025', 1, [r'FOLIO: 25014300', r'FECHA 28ENE25'], True, None),
 ('Extractor', 'Cuenta predial', 'U0003410', 1, [r'NÚMERO DE CUENTA'], True, None),
 ('Extractor', 'Clave catastral', '6301144006', 1, [r'CLAVE CATASTRAL: 6301144006'], True, None),
 ('Extractor', 'Valor catastral', '$1,255,636.55', 1, [r'VALOR CATASTRAL: 1255636'], True, 'La escritura cita un avalúo catastral distinto ($1,540,154.81, folio 04660A); el recibo trae el valor catastral registrado.'),
 ('Extractor', 'Importe pagado', '$13,184.19 · pago anual con descuento', 1, [r'TOTAL A PAGAR: \$13,184\.19'], True, None),
 ('Extractor', 'Titular actual', 'No consta en el recibo', 1, [r'PAGO DE IMPUESTO PREDIAL'], False,
   'Es un comprobante de terminal bancaria: no imprime contribuyente, ubicación ni superficie. Para contrastar el titular y la dirección hace falta la boleta o constancia de no adeudo.'),
]
ALI = [
 ('Extractor', 'Tipo documental', 'Constancia de alineamiento y número oficial', 1, [r'CONSTANCIA DE ALINEAMIENTO', r'Y NÚMERO OFICIAL'], True, None),
 ('Extractor', 'Autoridad emisora', 'Secretaría de Desarrollo Urbano y Ordenamiento Territorial · Tepeji del Río', 1, [r'Secretaría de Desarrollo', r'Urbano y Ordenamiento', r'^Territorial'], True, None),
 ('Extractor', 'Folio', 'ALIN/151/2025', 1, [r'ALIN/151/2025'], True, None),
 ('Extractor', 'Fecha de expedición', '21 de abril de 2025', 2, [r'Tepeji del Rio de Ocampo, Hidalgo; a', r'^ABRIL', r'21 de_', r'de 2025'], True, None),
 ('Extractor', 'Titular actual', 'José Haber Douek', 1, [r'JOSE HABER DOUEK'], True, 'Solicitante de la constancia.'),
 ('Extractor', 'Número oficial', '298', 2, [r'298 \(DOCIENTOS NOVENTA Y OCHO\)'], True, None),
 ('Extractor', 'Dirección del inmueble', 'Calle Melchor Ocampo, Colonia Atengo, Tepeji del Río de Ocampo, Hidalgo', 2, [r'MELCHOR OCAMPO', r'COLONIA ATENGO'], True, None),
 ('Extractor', 'Identificación del predio', 'Lote 03, Manzana 141, Colonia Atengo', 2, [r'Lote:', r'^03$', r'Manz\.:', r'^141$'], True, None),
 ('Extractor', 'Vigencia', 'Seis meses desde la expedición: venció el 21 de octubre de 2025', 1, [r'ESTA CONSTANCIA DE ALNEAMIENTO', r'EXPEDICIÓN, DE CONFORMIDAD'], False,
   'La constancia tiene vigencia de seis meses (arts. 30 y 31 del Reglamento de Construcción). A la fecha de hoy ya venció.'),
]
USO = [
 ('Extractor', 'Tipo documental', 'Información técnica de uso de suelo (no es licencia ni constancia)', 1, [r'ASUNTO: INFORMACION TECNICA'], True, 'El propio documento lo aclara en el punto 3 de la página 2.'),
 ('Extractor', 'Autoridad emisora', 'Secretaría de Desarrollo Urbano y Ordenamiento Territorial · Tepeji del Río', 1, [r'^Secretaría de Desarrollo', r'^Urbano y Ordenamiento', r'^Territorial'], True, None),
 ('Extractor', 'Folio', 'SDUOT/154/25 · Expediente 284-25', 1, [r'SDUOT/154/25', r'EXPEDIENTE: 284-25'], True, None),
 ('Extractor', 'Fecha de expedición', '23 de abril de 2025', 1, [r'Tepeji del Río de Ocampo a 23 de abril'], True, None),
 ('Extractor', 'Titular actual', 'José Haber Douek', 1, [r'JOSE HABER DOUEK'], True, 'Solicitante.'),
 ('Extractor', 'Dirección del inmueble', 'Paso del Norte, Avenida Melchor Ocampo, Barrio de Atengo, Tepeji del Río de Ocampo', 1,
   [r'DE SUELO del predio ubicado en', r'BARRIO DE ATENGO, perteneciente'], True, None),
 ('Extractor', 'Identificación del predio', 'El Paso del Norte', 1, [r'DE SUELO del predio ubicado en'], True, None),
 ('Extractor', 'Uso de suelo', 'Habitacional de media densidad (HMD, 51 a 200 hab./ha)', 2, [r'inmueble se encuentra en una zona urbanizable', r'HMD \(habitacional media densidad\)'], False,
   'La zona es habitacional de media densidad y el documento no autoriza el uso comercial: no es licencia ni constancia de uso de suelo.'),
 ('Extractor', 'Vigencia', '180 días naturales: venció el 20 de octubre de 2025', 2, [r'El presente documento es INTRANSFERIBLE', r'naturales y es exclusivamente'], False,
   'Intransferible y de 180 días naturales desde el 23 de abril de 2025. A la fecha de hoy ya venció.'),
]

CONJ = [
 ('esc', 'tepeji5-escritura', 'escrituras', 'Escrituras_Tepeji del Río 5.pdf', f'{DOCS}/Escrituras/Escritura/Escrituras_Tepeji_del_Rio_5.pdf', 'Compraventa · Tepeji del Río · Notaría 101', ESC),
 ('pre', 'tepeji5-predial', 'predial', '1. Predial 2025 Tepeji 5.pdf', f'{DOCS}/Predial/Predial/1. Predial 2025 Tepeji 5.pdf', 'Predial 2025 · Tepeji del Río · cuenta U0003410', PRE),
 ('ali', 'tepeji5-alineamiento', 'alineamiento', '3. Alineamiento y numero oficial  Tepeji 5.pdf', f'{DOCS}/Alineamiento_y_Numero_Oficial/Alineamiento_y_Numero_Oficial/3. Alineamiento y numero oficial  Tepeji 5.pdf', 'Alineamiento y número oficial · Tepeji del Río · No. 298', ALI),
 ('uso', 'tepeji5-uso', 'uso', 'USO DE SUELO TEPEJI DEL RIO 5.pdf', f'{DOCS}/Uso_de_suelo/Uso_de_suelo/USO DE SUELO TEPEJI DEL RIO 5.pdf', 'Información técnica de uso de suelo · Tepeji del Río', USO),
]
indice_path = f'{RAIZ}/analisis/indice.json'
indice = [e for e in json.load(open(indice_path)) if e.get('grupo') != GRUPO]
for k, id_, tipo, original, ruta, titulo, pasos in CONJ:
    pags = cargar(k)
    out_pg = f'{RAIZ}/paginas/{id_}'; os.makedirs(out_pg, exist_ok=True)
    for p in pags: shutil.copy(f'{OCR}/{k}/p{p["pagina"]}.jpg', f'{out_pg}/p{p["pagina"]}.jpg')
    res = []
    for i, (ag, campo, valor, pag, pats, ok, nota) in enumerate(pasos, 1):
        rect, conf = caja(pags, pag, pats)
        d = {'pagina': pag, 'rect': rect, 'agente': ag, 'campo': campo, 'valor': valor, 'ok': ok, 'confianza': conf if ok else min(conf, 0.6), 'n': i, 't': '00:%04.1f' % (0.7 * i)}
        d['nota'] = nota or ''
        res.append(d)
    res.sort(key=lambda d: (d['pagina'], d['rect'][1])); 
    for i, d in enumerate(res, 1): d['n'] = i; d['t'] = '00:%04.1f' % (0.7 * i)
    an = {'id': id_, 'tipo': tipo, 'grupo': GRUPO, 'archivo': original, 'titulo': titulo,
          'paginas': [{'n': p['pagina'], 'img': f'paginas/{id_}/p{p["pagina"]}.jpg', 'w': p['w'], 'h': p['h']} for p in pags],
          'total_paginas': len(pags), 'pasos': res,
          'resumen': {'validados': sum(1 for d in res if d['ok']), 'revisar': sum(1 for d in res if not d['ok'])}}
    json.dump(an, open(f'{RAIZ}/analisis/{id_}.json', 'w'), ensure_ascii=False, indent=1)
    indice.append({'id': id_, 'tipo': tipo, 'grupo': GRUPO, 'archivo': original, 'originales': [original, os.path.basename(ruta)], 'bytes': os.path.getsize(ruta),
                   'titulo': titulo, 'paginas': len(pags), 'pasos': len(res), 'revisar': sum(1 for d in res if not d['ok'])})
    print(id_, len(pags), 'páginas', len(res), 'pasos', sum(1 for d in res if not d['ok']), 'para revisar')
json.dump(indice, open(indice_path, 'w'), ensure_ascii=False, indent=1)
