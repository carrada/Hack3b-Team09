"""Pruebas de extremo a extremo: abren las páginas en un navegador WebKit sin ventana (pruebas/captura.swift),
ejecutan acciones reales y comprueban el resultado. Necesita el servidor local:  python3 -m http.server 8000
Ejecutar:  python3 pruebas/e2e.py [--capturas carpeta] [--solo texto_del_nombre]"""
import json, os, re, subprocess, sys, tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get('BASE', 'http://localhost:8000')
BIN = os.path.join(tempfile.gettempdir(), 'captura3b')
SALIDA = sys.argv[sys.argv.index('--capturas') + 1] if '--capturas' in sys.argv else os.path.join(tempfile.gettempdir(), 'capturas3b')

def compilar():
    fuente = os.path.join(RAIZ, 'pruebas', 'captura.swift')
    if not os.path.exists(BIN) or os.path.getmtime(BIN) < os.path.getmtime(fuente):
        subprocess.run(['swiftc', '-O', '-o', BIN, fuente], check=True)

# Cada paso: (js, espera_ms[, png]). El js devuelve 'OK' o un texto con el motivo del fallo.
def ok(cond, msg): return f"({cond}) ? 'OK' : 'FALLA: {msg}'"
def estado_rev(): return "__revision.estado()"

PRUEBAS = {
 'revision · modo automático: solo el rectángulo se ve claro': ('revision.html?exp=t1&doc=01-escritura-1', [
   (ok("__revision.estado().paso === 0 && __revision.estado().N === 11", 'estado inicial'), 600),
   (ok("!document.getElementById('capaBase').classList.contains('enfoque')", 'al inicio la página debe verse completa y nítida'), 100),
   ("__revision.ir(5, false); 'OK'", 1800, 'rev_paso5.png'),
   (ok("document.getElementById('capaBase').classList.contains('enfoque')", 'con un agente leyendo, el resto debe estar borroso'), 100),
   (ok("getComputedStyle(document.getElementById('capaBase')).filter.indexOf('blur') >= 0", 'la capa base debe tener blur'), 100),
   (ok("document.querySelectorAll('.caja.v').length === 1", 'debe haber un solo rectángulo'), 100),
   (ok("(function(){var c=document.querySelector('.caja.v'); var p=JSON.parse(window.__pasos)[4]; return Math.abs(parseFloat(c.style.left)-p.rect[0]*100)<0.01 && Math.abs(parseFloat(c.style.top)-p.rect[1]*100)<0.01})()", 'el rectángulo debe estar donde dice el análisis'), 100),
   (ok("document.querySelector('.capa.nitida').style.clipPath.indexOf('inset') === 0", 'la copia nítida debe estar recortada al rectángulo'), 100),
   ("__revision.ir(__revision.estado().N + 1, false); 'OK'", 1500, 'rev_fin_auto.png'),
   (ok("__revision.estado().terminado && document.querySelectorAll('.caja.v').length === 2", 'al terminar quedan 2 zonas para revisión humana'), 100),
 ], "window.__pasos = null; fetch('analisis/01-escritura-1.json').then(r=>r.text()).then(t=>{window.__pasos=JSON.stringify(JSON.parse(t).pasos)}); 'OK'"),

 'revision · reproducción automática avanza sola y se puede pausar': ('revision.html?exp=t1b&doc=01-escritura-1', [
   ("document.getElementById('btnPlay').click(); 'OK'", 3400),
   (ok("__revision.estado().paso >= 2", 'tras ~3 s el agente debe haber pasado al paso 2'), 100),
   ("document.getElementById('btnPlay').click(); 'OK'", 3500),   # pausar
   ("window.__p = __revision.estado().paso; 'OK'", 3500),
   (ok("__revision.estado().paso === window.__p", 'en pausa no debe avanzar'), 100),
 ], None),

 'revision · modo manual: decisiones, corrección, guardado y veredicto': ('revision.html?exp=t2&doc=01-escritura-1&modo=manual', [
   (ok("__revision.estado().modo === 'manual' && __revision.estado().paso === 1", 'debe abrir en el punto 1'), 800),
   ("document.querySelector('[data-dec=ok]').click(); 'OK'", 400),
   ("document.querySelector('[data-dec=fix]').click(); 'OK'", 400),
   (ok("!!document.getElementById('valCorr')", 'Corregir debe abrir el editor'), 100),
   ("document.getElementById('valCorr').value = 'Valor corregido por una persona'; document.getElementById('gCorr').click(); 'OK'", 400),
   ("document.querySelector('[data-dec=no]').click(); 'OK'", 400),
   (ok("(function(){var e=JSON.parse(localStorage.getItem('exp3b')).t2; var d=e.dec['01-escritura-1']; return d[1]==='ok'&&d[2]==='fix'&&d[3]==='no'&&e.corr['01-escritura-1'][2]==='Valor corregido por una persona'})()", 'las decisiones y la corrección deben guardarse'), 100),
   ("for (var k=0;k<30 && !__revision.estado().terminado;k++){var b=document.querySelector('[data-dec=ok]'); if(b) b.click();} 'OK'", 1800, 'rev_manual_fin.png'),
   (ok("__revision.estado().terminado && /No cumple/.test(document.getElementById('cuerpoLado').innerText)", 'con un «No cumple» el veredicto debe ser No cumple'), 100),
   (ok("document.querySelectorAll('.caja.v').length === 11", 'al terminar se muestran los 11 puntos con su resultado'), 100),
 ], None),

 'revision · escaneo desvanecido: nada validado, todo para verificación humana': ('revision.html?exp=t3&doc=01-escritura', [
   (ok("__revision.estado().N === 7 && __revision.estado().id === '01-escritura'", 'documento ilegible cargado'), 600),
   ("document.getElementById('btnManual').click(); 'OK'", 1500, 'rev_ilegible.png'),
   (ok("/No legible/.test(document.getElementById('cuerpoLado').innerText) || /Contraste bajo/.test(document.getElementById('cuerpoLado').innerText)", 'debe mostrar que el agente no pudo leerlo'), 100),
   (ok("document.querySelectorAll('.punto .a').length === 7 && Array.from(document.querySelectorAll('.punto .a')).every(function(e){return /revisar/.test(e.innerText)})", 'los 7 puntos deben venir marcados «agente: revisar»'), 100),
 ], None),

 'analizador · revisión humana sobre el PDF': ('analizador.html?exp=t4&doc=01-escritura-1', [
   (ok("__analizador.estado().pendientes === 2 && __analizador.estado().hallazgos === 2", 'deben quedar 2 hallazgos pendientes'), 900),
   (ok("/Requiere revisión/.test(document.getElementById('vTexto').innerText) && /3\\s*documentos faltantes/.test(document.getElementById('razones').innerText.replace(/\\s+/g,' '))", 'el veredicto explica por qué: 3 documentos faltantes'), 100),
   (ok("document.querySelectorAll('.doc.falta').length === 3", 'los 3 documentos faltantes aparecen marcados'), 100),
   ("document.querySelector('[data-d^=ok]').click(); 'OK'", 600),
   (ok("__analizador.estado().pendientes === 1 && /por ti · hoy/.test(document.body.innerText)", 'confirmar baja los pendientes y deja registro con hora'), 100),
   ("document.querySelector('.hall:not(.sel) > button').click(); 'OK'", 500),
   (ok("!!document.querySelector('.det table') && /Fundamento/.test(document.querySelector('.det').innerText) && /Siguiente paso/.test(document.querySelector('.det').innerText)", 'el hallazgo muestra qué dice cada documento, fundamento y siguiente paso'), 100),
   ("document.querySelector('[data-d^=no]').click(); 'OK'", 600),
   (ok("document.getElementById('vTexto').innerText === 'No cumple' && /por ti · /.test(document.querySelector('.audit').innerText)", 'con un «No cumple» la recomendación es No cumple y queda registro con hora'), 100),
   ("document.querySelector('[data-d^=undo]').click(); 'OK'", 500),
   (ok("__analizador.estado().pendientes === 2 - 1", 'Deshacer reabre el hallazgo'), 100),
   ("document.getElementById('chkDim').click(); 'OK'", 300),
   (ok("Array.from(document.querySelectorAll('.pagina > img')).every(function(i){return i.style.opacity==='1'}) && document.querySelectorAll('.nitida').length===0", 'sin atenuación la página se ve completa'), 100),
   ("document.getElementById('btnSubir') ; document.querySelector('[data-doc=predial]').click(); 'OK'", 700),
   (ok("/Documento faltante/i.test(document.getElementById('scroll').innerText) && /bloqueada/.test(document.getElementById('scroll').innerText)", 'un documento faltante muestra qué validaciones bloquea'), 100),
   ("document.getElementById('btnSolic').click(); 'OK'", 600),
   (ok("/Solicitado/.test(document.getElementById('scroll').innerText) && /solicitado/.test(document.getElementById('listaDocs').innerText)", 'Solicitar documento queda registrado'), 100),
 ], None),

 'validación cruzada · comparar datos entre documentos': ('validacion.html?exp=t5&doc=01-escritura-1', [
   ("localStorage.setItem('exp3b', JSON.stringify({t5:{docs:{escrituras:{analisis:'01-escritura-1',archivo:'01 Escritura_1.pdf'}}}})); location.reload(); 'OK'", 2500),
   (ok("document.querySelectorAll('#tabs button').length === 6 && document.querySelectorAll('#cols .col').length === 4", 'hay 6 datos y 4 documentos en paralelo'), 800),
   (ok("__validacion.estado().resultados.every(function(r){return r==='pen'})", 'con un solo documento nada se da por coincidente'), 100),
   (ok("/no recibido/.test(document.getElementById('cols').innerText) && /Sin dato en/.test(document.getElementById('banda').innerText)", 'los documentos faltantes se muestran como no recibidos'), 100),
   ("__validacion.elegir('superficie'); 'OK'", 800),
   (ok("/245\\.00/.test(document.getElementById('cols').innerText) && document.querySelectorAll('.hojita .c').length===1", 'la superficie de la escritura se ve con su rectángulo'), 100),
   ("__validacion.correr(); 'OK'", 1500),
   (ok("__validacion.estado().fase === 'corre' && __validacion.estado().vistos < 6", 'al analizar se revelan los datos de uno en uno'), 100),
   ("'OK'", 9500),
   (ok("__validacion.estado().fase === 'listo' && __validacion.estado().vistos === 6", 'termina y deja los 6 datos revisados'), 100),
 ], None),

 'mapa · tienda: al abrirla la cámara hace zoom y el panel muestra su expediente': ('index.html?fijo=1', [
   ("localStorage.clear(); location.reload(); 'OK'", 8000),
   ("window.__c0 = map.getZoom(); document.querySelector('[data-v=tiendas]').click(); 'OK'", 400),
   (ok("document.querySelectorAll('.card[data-t]').length === 62", 'la lista de tiendas trae las 62'), 100),
   ("document.querySelector('.card[data-t]').click(); 'OK'", 8000, 'mapa_tienda.png'),
   ("(document.body.classList.contains('exp') && map.getZoom() > 16) ? 'OK' : 'FALLA: al abrir una tienda el mapa debe acercarse (zoom > 16); zoom=' + map.getZoom().toFixed(1) + ' moviendo=' + map.isMoving()", 100),
   (ok("/Documentos\\s*0\\/4/.test(document.querySelector('.tabs2').innerText)", 'una tienda nueva muestra 0/4 documentos'), 100),
   (ok("/Subir documentos/.test(document.getElementById('drawer').innerText)", 'el panel indica el siguiente paso: subir documentos'), 100),
   ("document.getElementById('dCerrar').click(); 'OK'", 700),
   (ok("!document.body.classList.contains('exp') && document.querySelector('[data-v=tiendas]').classList.contains('on')", 'al cerrar vuelve la lista de tiendas'), 100),
 ], None),
 'mapa · zona real: datos clave, cruce y salto a verificación humana': ('index.html?fijo=1', [
   ("localStorage.clear(); location.reload(); 'OK'", 8000),
   (ok("EXPS.length === 21 && EXPS.every(e => Object.keys(Estado.get(e.id).docs).length > 0)", 'los 21 expedientes ya traen sus documentos asignados'), 100),
   ("document.querySelector('.card[data-e=tepeji5]').click(); 'OK'", 4500, 'mapa_zona.png'),
   (ok("document.body.classList.contains('exp') && map.getZoom() > 14", 'al abrir una zona el mapa se acerca'), 100),
   (ok("/Documentos\\s*4\\/4/.test(document.querySelector('.tabs2').innerText)", 'Tepeji 5 tiene los 4 documentos'), 100),
   (ok("/José Haber Douek/.test(document.querySelector('.clave').innerText) && /298/.test(document.querySelector('.clave').innerText)", 'Datos clave muestra el titular y el número oficial 298'), 100),
   (ok("/3 datos difieren/.test(document.querySelector('.clave').innerText)", 'Datos clave destaca los 3 datos que difieren'), 100),
   (ok("/hallazgos esperan tu verificación/.test(document.querySelector('.paso').innerText) && /analizador\\.html\\?exp=tepeji5/.test(document.getElementById('lnkPaso').href)", 'el paso recomendado lleva a verificación humana'), 100),
   (ok("document.querySelector('.est-b').innerText.indexOf('por revisar') >= 0", 'la etiqueta de estado coincide con los hallazgos'), 100),
 ], None),
 'mapa · investigación en lote: elegir zonas, analizar juntas y pasar a verificación humana': ('index.html?fijo=1', [
   ("localStorage.clear(); location.reload(); 'OK'", 8000),
   ("['tepeji5','mirador','crispin'].forEach(id => document.querySelector('[data-inv=' + id + ']').click()); 'OK'", 600),
   (ok("Object.keys(inv).length === 3 && /3 zonas en investigación/.test(document.getElementById('barraSel').innerText)", 'tres zonas elegidas y contadas en la barra de selección'), 100),
   (ok("/3 sin analizar/.test(document.getElementById('barraSel').innerText)", 'las tres quedan sin analizar'), 100),
   ("document.getElementById('btnAnalizarInv').click(); 'OK'", 9000, 'mapa_lote.png'),
   (ok("/3 con detalles/.test(document.getElementById('barraSel').innerText)", 'el análisis en lote termina para las tres'), 100),
   (ok("/analizador\\.html\\?exp=/.test(document.getElementById('lnkVerificar').href)", 'hay un enlace directo a verificación humana'), 100),
   ("document.querySelector('[data-k=\"En investigación\"]').click(); 'OK'", 400),
   (ok("document.querySelectorAll('.card[data-e]').length === 3", 'el filtro «En investigación» muestra solo las tres'), 100),
   ("document.getElementById('btnQuitarInv').click(); 'OK'", 400),
   (ok("Object.keys(inv).length === 0 && document.getElementById('barraSel').hidden", 'Quitar vacía la investigación y oculta la barra'), 100),
 ], None),
 'mapa · al recargar: vista del mundo con el logo y a los 2 s vuelo a la vista cercana': ('index.html', [
   (ok("map.getZoom() < 5 && +document.querySelector('.logo-mx').style.opacity > 0.5", 'al cargar se ve el mundo con el logo de 3B sobre México'), 100),
   (ok("(function(){ var p = map.project([-99.13, 19.40]), c = map.getContainer().getBoundingClientRect(); var r = document.querySelector('.logo-mx').getBoundingClientRect(); return Math.abs((r.left + r.width / 2) - (c.left + p.x)) < 8 && Math.abs((r.top + r.height / 2) - (c.top + p.y)) < 8 })()", 'el logo queda sobre México'), 9500),
   (ok("map.getZoom() > 10 && map.getPitch() > 40 && +document.querySelector('.logo-mx').style.opacity === 0", 'después del vuelo está en la vista cercana y el logo ya no estorba'), 100),
 ], None),

 'mapa 3D · modelo, luces y regla de tamaño': ('index.html?fijo=1', [
   ("document.getElementById('btnOcultar').click(); 'OK'", 8500),
   ("/*las 62 tiendas tienen su capa de modelo*/ (function(){var f=TIENDAS.filter(function(t){return !map.getLayer('tm-'+t.id)}); return f.length===0 ? 'OK' : 'FALLA: faltan capas de modelo en '+f.length+' tiendas'})()", 100),
   ("/*el modelo está cargado y Mapbox no oculta tiendas por densidad*/ (function(){var mal=TIENDAS.filter(function(t){return map.getLayoutProperty('tm-'+t.id,'model-id')!=='tienda3b' || map.getLayoutProperty('tm-'+t.id,'model-allow-density-reduction')!==false}); return map.hasModel('tienda3b') && mal.length===0 ? 'OK' : 'FALLA: el modelo no está cargado o se permite ocultar modelos ('+mal.length+')'})()", 100),
   ("/*las luces 3D están activas*/ (function(){var l=map.getLights(); return l && l.length===2 ? 'OK' : 'FALLA: las luces 3D no están activas'})()", 100),
   # --- la regla de tamaño, sin perspectiva: continua, nunca menor al mínimo, real de cerca, nunca crece al acercar
   ("""/*la regla de tamaño es continua, respeta el mínimo y de cerca da el tamaño real*/ (function(){ camara = null; var ejemplos=[TIENDAS.find(function(t){return t.esc<0.8}), TIENDAS.find(function(t){return t.esc>1.6}), TIENDAS[0]]; var err=[];
      ejemplos.forEach(function(t){ var ant=null; for (var z=8; z<=22; z+=0.25) { var s=escalaNum(t,z); var px=s*MODELO_LARGO/metrosPorPx(z,t.coords[1]);
        if (px < PX_MIN*0.99) err.push('px '+px.toFixed(1)+' < mínimo en z'+z);
        if (ant!==null) { if (s>ant*1.0001) err.push('la escala crece al acercar en z'+z); if (s/ant < 0.84*0.99) err.push('salto brusco en z'+z+' ('+(s/ant).toFixed(2)+')'); }
        ant=s; }
        var real=Math.max(0.8,Math.min(1.6,t.esc||1)); var sc=escalaNum(t,21); if (Math.abs(sc/real-1)>0.02) err.push('de cerca no mide su tamaño real ('+sc.toFixed(2)+' vs '+real+')'); });
      medirCamara(); return err.length===0 ? 'OK' : 'FALLA: '+err.slice(0,3).join('; ') })()""", 100),
   # --- perspectiva: con la cámara inclinada todas deben verse del mismo tamaño en pantalla
   ("map.jumpTo({center:[-99.14,19.43],zoom:13.5,pitch:60,bearing:-15}); 'OK'", 4500),
   ("""/*con la cámara inclinada todas se ven del mismo tamaño en pantalla*/ (function(){ var px=[]; TIENDAS.forEach(function(t){ var p=map.project(t.coords); if (p.x<0||p.y<0||p.x>innerWidth-76||p.y>innerHeight) return;
        var s=map.getPaintProperty('tm-'+t.id,'model-scale')[0], W=MODELO_LARGO*s, d=W/(111320*Math.cos(t.coords[1]*Math.PI/180)); var q=map.project([t.coords[0]+d,t.coords[1]]);
        px.push(Math.hypot(q.x-p.x,q.y-p.y)); });
      var mn=Math.min.apply(null,px), mx=Math.max.apply(null,px), media=px.reduce(function(a,b){return a+b},0)/px.length;
      window.__px=[px.length,mn.toFixed(1),mx.toFixed(1),media.toFixed(1)].join(' / ');
      return px.length>=10 && mx/mn<1.5 && media>28 && media<50 ? 'OK' : 'FALLA: tamaños en pantalla (n / mín / máx / media): '+window.__px })()""", 100),
   # --- se ven las 62 tiendas al alejar el mapa
   ("map.jumpTo({center:[-99.14,19.38],zoom:10,pitch:0,bearing:0}); 'OK'", 5000),
   ("""/*se ven las 62 tiendas al alejar el mapa*/ (function(){ var dentro=TIENDAS.filter(function(t){var p=map.project(t.coords); return p.x>0&&p.x<innerWidth-76&&p.y>0&&p.y<innerHeight}).length;
      var ids={}; map.queryRenderedFeatures({layers:['tiendas3b-area']}).forEach(function(f){ids[f.properties.id]=1});
      var n=Object.keys(ids).length; return dentro===62 && n>=60 ? 'OK' : 'FALLA: dentro de la pantalla '+dentro+', dibujadas '+n })()""", 100),
   # --- la escala se actualiza al hacer zoom
   ("map.jumpTo({center:[-99.127,19.4268],zoom:12,pitch:55}); 'OK'", 2500),
   ("window.__s12 = map.getPaintProperty('tm-'+TIENDAS[0].id,'model-scale')[0]; map.jumpTo({center:TIENDAS[0].coords,zoom:19.5}); 'OK'", 2500),
   ("/*la escala se actualiza al acercar y alejar*/ (function(){ var s19=map.getPaintProperty('tm-'+TIENDAS[0].id,'model-scale')[0]; return window.__s12 > s19*20 && Math.abs(s19/Math.max(0.8,Math.min(1.6,TIENDAS[0].esc||1))-1)<0.05 ? 'OK' : 'FALLA: s12='+window.__s12+' s19.5='+s19 })()", 100),
   # --- rendimiento: el mapa no debe congelarse al alejar y acercar (las sombras lo congelaban varios segundos)
   ("window.R=TIENDAS.find(function(t){return /Roldan 71/.test(t.dir)}); window.__c=[]; window.__n=0; (function t(){window.__n++; requestAnimationFrame(t)})(); window.__i=setInterval(function(){window.__c.push(window.__n); window.__n=0},1000); map.jumpTo({center:[-99.14,19.43],zoom:13.5,pitch:60,bearing:-15}); 'OK'", 7000),
   ("window.__lejos=window.__c.slice(1); window.__s1=sombras; window.__c=[]; map.jumpTo({center:R.coords,zoom:19.2,pitch:55,bearing:R.rot}); 'OK'", 7000),
   ("window.__cerca=window.__c.slice(1); window.__s2=sombras; window.__c=[]; map.jumpTo({center:[-99.14,19.43],zoom:13.5,pitch:60,bearing:-15}); 'OK'", 7000),
   ("""/*el mapa no se congela y las sombras solo se activan de cerca*/ (function(){ clearInterval(window.__i); var todo=window.__lejos.concat(window.__cerca, window.__c.slice(1)); var mn=Math.min.apply(null,todo);
      if (mn < 15) return 'FALLA: el mapa se congela (cuadros por segundo en cada tramo: '+JSON.stringify(todo)+')';
      if (window.__s1 !== false || window.__s2 !== true || sombras !== false) return 'FALLA: las sombras deben estar apagadas de lejos y encendidas de cerca ('+window.__s1+', '+window.__s2+', '+sombras+')';
      return 'OK' })()""", 100),
 ], None)
}

def correr():
    compilar(); os.makedirs(SALIDA, exist_ok=True)
    total = fallos = 0
    solo = sys.argv[sys.argv.index('--solo') + 1] if '--solo' in sys.argv else None
    for nombre, (url, pasos, preparar) in PRUEBAS.items():
        if solo and solo not in nombre: continue
        lista = [{'js': 'localStorage.removeItem("exp3b"); 1', 'espera': 0}] if False else []
        if preparar: lista.append({'js': preparar, 'espera': 500})
        indices = []
        for p in pasos:
            d = {'js': p[0], 'espera': p[1], 'imprime': True}
            if len(p) > 2: d['png'] = p[2]
            lista.append(d); indices.append(len(lista))
        ruta = os.path.join(tempfile.gettempdir(), 'pasos3b.json'); json.dump(lista, open(ruta, 'w'))
        t_espera = 1200
        r = subprocess.run([BIN, f'{BASE}/{url}', '1440', '900', ruta, SALIDA], capture_output=True, text=True, timeout=240)
        salida = {}
        for linea in r.stdout.splitlines():
            if linea.startswith('[') and '] ' in linea:
                k, v = linea[1:].split('] ', 1)
                if k.isdigit(): salida[int(k)] = v
        print(f'\n▸ {nombre}')
        for p, idx in zip(pasos, indices):
            v = salida.get(idx); es_check = 'FALLA' in p[0]
            m = re.match(r"\s*(?:\(?\s*)?/\*(.*?)\*/", p[0]) or re.search(r"'FALLA: ([^'+]*)", p[0])
            etiqueta = m.group(1).strip() if m else f'paso {idx}'
            if v == 'OK':
                if es_check: total += 1; print('   ✓', etiqueta)
                continue
            total += 1; fallos += 1; print('   ✗', etiqueta, '→', v or '(sin respuesta)')
        if 'FIN' not in r.stdout: fallos += 1; total += 1; print('   ✗ la prueba no terminó:', r.stdout[-200:])
    print(f'\n{total - fallos}/{total} comprobaciones correctas' + ('' if not fallos else f' · {fallos} FALLAS'))
    return 1 if fallos else 0

if __name__ == '__main__':
    sys.exit(correr())
