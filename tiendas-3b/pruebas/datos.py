"""Pruebas de los datos que produce el análisis (analisis/*.json) y de las páginas que usa la interfaz.
Ejecutar:  python3 pruebas/datos.py"""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPOS = {'n', 'pagina', 'rect', 'agente', 'campo', 'valor', 'ok', 'nota', 't'}

def cargar(ruta):
    with open(os.path.join(RAIZ, ruta), encoding='utf-8') as f: return json.load(f)

class PruebasDatos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indice = cargar('analisis/indice.json')
        cls.analisis = {d['id']: cargar(f"analisis/{d['id']}.json") for d in cls.indice}

    def test_hay_documentos(self):
        self.assertGreaterEqual(len(self.indice), 4)
        self.assertEqual(len({d['id'] for d in self.indice}), len(self.indice), 'ids repetidos')

    def test_tamanos_distintos_para_reconocer_archivos(self):
        tams = [d['bytes'] for d in self.indice]
        self.assertEqual(len(set(tams)), len(tams), 'dos documentos con el mismo tamaño: no se podrían distinguir al subirlos')

    def test_estructura_de_los_pasos(self):
        for id_, a in self.analisis.items():
            with self.subTest(doc=id_):
                self.assertTrue(a['pasos'], 'sin pasos')
                self.assertEqual([p['n'] for p in a['pasos']], list(range(1, len(a['pasos']) + 1)), 'numeración no consecutiva')
                for p in a['pasos']:
                    self.assertTrue(CAMPOS <= set(p), f"faltan campos en el paso {p.get('n')}")
                    self.assertIsInstance(p['ok'], bool)
                    self.assertTrue(p['valor'].strip())

    def test_rectangulos_dentro_de_la_pagina(self):
        for id_, a in self.analisis.items():
            for p in a['pasos']:
                x, y, w, h = p['rect']
                with self.subTest(doc=id_, paso=p['n']):
                    self.assertTrue(0 <= x < 1 and 0 <= y < 1 and w > 0 and h > 0, p['rect'])
                    self.assertLessEqual(x + w, 1.0001); self.assertLessEqual(y + h, 1.0001)
                    self.assertTrue(1 <= p['pagina'] <= len(a['paginas']))

    def test_imagenes_existen_y_con_proporcion_de_hoja(self):
        for id_, a in self.analisis.items():
            for pg in a['paginas']:
                ruta = os.path.join(RAIZ, pg['img'])
                with self.subTest(doc=id_, pagina=pg['n']):
                    self.assertTrue(os.path.exists(ruta), ruta)
                    # los documentos originales de la demostración son hojas verticales; los reales pueden ser fotos o comprobantes horizontales
                    self.assertGreater(pg['h'] / pg['w'], 1.2 if not a.get('grupo') else 0.5, 'proporción de la hoja')

    def test_documentos_claros_extraen_los_campos_clave(self):
        clave = {'Tipo documental', 'Autoridad emisora', 'Superficie del predio', 'Clave catastral', 'Precio de la operación', 'Dirección del inmueble'}
        legibles = [a for a in self.analisis.values() if not a.get('grupo') and a['resumen']['validados'] >= 6]
        self.assertGreaterEqual(len(legibles), 3)
        for a in legibles:
            with self.subTest(doc=a['id']):
                self.assertTrue(clave <= {p['campo'] for p in a['pasos']}, clave - {p['campo'] for p in a['pasos']})

    def test_la_superficie_se_contrasta_con_las_medidas(self):
        for a in [x for x in self.analisis.values() if not x.get('grupo')]:      # solo las escrituras de la demostración traen la comparación con medidas
            sup = [p for p in a['pasos'] if p['campo'] == 'Superficie del predio']
            if sup and sup[0]['ok']:
                with self.subTest(doc=a['id']):
                    self.assertIn('Coincide con las medidas', sup[0]['nota'])

    def test_escaneo_ilegible_no_inventa_datos(self):
        malos = [a for a in self.analisis.values() if a['resumen']['validados'] == 0]
        self.assertTrue(malos, 'debe haber al menos un caso ilegible para demostrar la verificación humana')
        for a in malos:
            with self.subTest(doc=a['id']):
                self.assertTrue(all(not p['ok'] for p in a['pasos']), 'un documento ilegible no debe dar datos por validados')
                self.assertTrue(all(p['valor'] in ('No legible', 'Contraste bajo · texto tenue') for p in a['pasos']))

    def test_resumen_coherente(self):
        for a in self.analisis.values():
            with self.subTest(doc=a['id']):
                self.assertEqual(a['resumen']['validados'] + a['resumen']['revisar'], len(a['pasos']))



class PruebasModelo(unittest.TestCase):
    """Verifica el archivo del modelo 3D (modelos/tienda.glb) y los datos de las tiendas (tiendas.js)."""
    @classmethod
    def setUpClass(cls):
        import struct
        ruta = os.path.join(RAIZ, 'modelos', 'tienda.glb')
        cls.tam = os.path.getsize(ruta)
        with open(ruta, 'rb') as f:
            magia, ver, total = struct.unpack('<4sII', f.read(12))
            cls.cabecera = (magia, ver, total)
            largo, tipo = struct.unpack('<I4s', f.read(8))
            cls.gltf = json.loads(f.read(largo))
        a = cls.gltf['accessors']; prim = cls.gltf['meshes'][0]['primitives'][0]
        cls.pos = a[prim['attributes']['POSITION']]
        with open(os.path.join(RAIZ, 'tiendas.js'), encoding='utf-8') as f:
            t = f.read()
        cls.tiendas = json.loads(t[t.index('['):t.rindex(']') + 1])

    def test_es_un_glb_valido_y_ligero(self):
        self.assertEqual(self.cabecera[0], b'glTF'); self.assertEqual(self.cabecera[1], 2)
        self.assertEqual(self.cabecera[2], self.tam, 'tamaño declarado distinto al real')
        self.assertLess(self.tam, 4 * 1024 * 1024, 'pesa demasiado para 62 tiendas')

    def test_cabe_en_el_limite_de_mapbox(self):
        self.assertLessEqual(self.pos['count'], 65536, 'Mapbox admite como máximo 65,536 vértices por malla')
        self.assertEqual(len(self.gltf['meshes']), 1, 'una sola malla')

    def test_dimensiones_y_orientacion(self):
        mn, mx = self.pos['min'], self.pos['max']
        ancho, alto, fondo = mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]      # glTF: Y es la altura
        self.assertAlmostEqual(ancho, 7.68, delta=0.1); self.assertAlmostEqual(alto, 3.0, delta=0.1); self.assertAlmostEqual(fondo, 5.69, delta=0.1)
        self.assertAlmostEqual(mn[1], 0.0, delta=0.05, msg='la base debe quedar en el suelo (y = 0)')

    def test_trae_texturas_y_normales(self):
        self.assertGreaterEqual(len(self.gltf['images']), 2)
        mat = self.gltf['materials'][0]
        self.assertIn('baseColorTexture', mat['pbrMetallicRoughness']); self.assertIn('normalTexture', mat)
        self.assertIn('NORMAL', self.gltf['meshes'][0]['primitives'][0]['attributes'])
        self.assertIn('TEXCOORD_0', self.gltf['meshes'][0]['primitives'][0]['attributes'])

    def test_datos_de_las_tiendas(self):
        t = self.tiendas
        self.assertEqual(len(t), 62)
        self.assertEqual(len({x['id'] for x in t}), 62, 'ids repetidos')
        for x in t:
            with self.subTest(tienda=x['dir']):
                lng, lat = x['coords']
                self.assertTrue(-99.37 <= lng <= -98.94 and 19.04 <= lat <= 19.60, 'fuera de la CDMX')
                self.assertTrue(0.3 <= x.get('esc', 1) <= 3.5)
                self.assertTrue(0 <= x.get('rot', 0) < 360)

    def test_ninguna_tienda_encima_de_otra(self):
        import math
        for i, a in enumerate(self.tiendas):
            for b in self.tiendas[i + 1:]:
                d = math.dist(((a['coords'][0] - b['coords'][0]) * 105000, (a['coords'][1] - b['coords'][1]) * 110540), (0, 0))
                if d < 10: self.assertTrue(a['dir'] != b['dir'] and d >= 10, f"{a['dir']} y {b['dir']} están a {d:.0f} m")


class PruebasExpedientes(unittest.TestCase):
    """analisis/expedientes.json: un expediente por predio, con los documentos que ya tenemos."""
    @classmethod
    def setUpClass(cls):
        cls.exps = cargar('analisis/expedientes.json'); cls.indice = {d['id']: d for d in cargar('analisis/indice.json')}

    def test_ids_unicos_y_documentos_existen(self):
        self.assertEqual(len({e['id'] for e in self.exps}), len(self.exps))
        for e in self.exps:
            with self.subTest(exp=e['id']):
                self.assertTrue(e['docs'], 'un expediente sin documentos')
                for tipo, id_ in e['docs'].items():
                    self.assertIn(tipo, ('escrituras', 'predial', 'alineamiento', 'uso'))
                    self.assertIn(id_, self.indice)
                    self.assertEqual(self.indice[id_].get('tipo', 'escrituras'), tipo)

    def test_ningun_documento_en_dos_expedientes(self):
        usados = [i for e in self.exps for i in list(e['docs'].values()) + e.get('extras', [])]
        self.assertEqual(len(usados), len(set(usados)), 'un documento asignado a dos expedientes')

    def test_se_pueden_ubicar_o_son_sinteticos(self):
        for e in self.exps:
            with self.subTest(exp=e['id']):
                self.assertTrue(e.get('busqueda') or e.get('coords') or e.get('sintetico'), 'sin forma de ubicarlo en el mapa')


if __name__ == '__main__':
    unittest.main(verbosity=2)
