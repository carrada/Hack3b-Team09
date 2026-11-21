/* Datos y estado compartidos entre las pantallas (mapa, analizador y revisión por agentes).
 *
 * Contrato con el backend: el análisis de cada PDF llega como `analisis/<id>.json`
 *   { id, archivo, titulo, paginas:[{n,img,w,h}], pasos:[{n,pagina,rect,agente,campo,valor,ok,nota,t}], resumen }
 * donde rect = [x, y, ancho, alto] normalizado (0..1, origen arriba a la izquierda).
 * Mientras no haya backend, esos archivos los genera un script local (OCR + reglas) con el mismo formato. */
(function () {
  const LLAVE = 'exp3b';
  const cache = {};

  // Recibe PDFs y los clasifica: los que reconoce (por nombre y tamaño) quedan como Escritura analizada; los demás, en cola.
  async function recibir(exp, files, tipo) {
    const docs = Object.assign({}, Estado.get(exp).docs), msgs = [];
    for (const file of files) {
      if (!/\.pdf$/i.test(file.name) && file.type !== 'application/pdf') { msgs.push(file.name + ': no es un PDF'); continue; }
      const m = await Datos.buscarPorArchivo(file);
      if (m) { const k = m.tipo || 'escrituras'; docs[k] = { analisis: m.id, archivo: file.name }; msgs.push(file.name + ' → clasificado como ' + nombreTipo(k)); }
      else if (tipo) { docs[tipo] = { archivo: file.name }; msgs.push(file.name + ' recibido; el backend lo analizará'); }
      else msgs.push(file.name + ': aún no hay análisis disponible');
    }
    Estado.set(exp, { docs }); return msgs;
  }

  const Datos = {
    async indice() {
      if (!cache.indice) cache.indice = await (await fetch('analisis/indice.json')).json();
      return cache.indice;
    },
    async expedientes() {
      if (!cache.expedientes) { const r = await fetch('analisis/expedientes.json'); cache.expedientes = r.ok ? await r.json() : []; }
      return cache.expedientes;
    },
    async analisis(id) {
      if (!cache[id]) {
        const r = await fetch(`analisis/${encodeURIComponent(id)}.json`);
        if (!r.ok) throw new Error('No existe el análisis ' + id);
        cache[id] = await r.json();
      }
      return cache[id];
    },
    // un archivo PDF elegido por el usuario se reconoce por nombre y tamaño (el backend real lo analizaría)
    async buscarPorArchivo(file) {
      const idx = await this.indice();
      return idx.find(d => d.bytes === file.size && (d.originales || []).includes(file.name))
          || idx.find(d => d.bytes === file.size) || null;
    }
  };

  /* ----- estado por expediente (se guarda en este navegador) ----- */
  function leer() { try { return JSON.parse(localStorage.getItem(LLAVE)) || {}; } catch (e) { return {}; } }
  function escribir(o) { try { localStorage.setItem(LLAVE, JSON.stringify(o)); } catch (e) {} }
  const Estado = {
    get(exp) {
      const e = leer()[exp] || {};
      return { docs: e.docs || {}, dec: e.dec || {}, corr: e.corr || {}, tiempos: e.tiempos || {}, solic: e.solic || {}, rec: e.rec || '', razones: e.razones || '' };
    },
    set(exp, cambios) { const t = leer(); t[exp] = Object.assign(this.get(exp), cambios); escribir(t); return t[exp]; },
    // decisión humana sobre un paso del análisis: 'ok' | 'fix' | 'no' | null
    decidir(exp, analisis, paso, valor, corregido) {
      const e = this.get(exp);
      e.dec[analisis] = e.dec[analisis] || {}; e.corr[analisis] = e.corr[analisis] || {}; e.tiempos[analisis] = e.tiempos[analisis] || {};
      if (valor) { e.dec[analisis][paso] = valor; e.tiempos[analisis][paso] = Date.now(); }
      else { delete e.dec[analisis][paso]; delete e.tiempos[analisis][paso]; }
      if (corregido) e.corr[analisis][paso] = corregido; else if (valor !== 'fix') delete e.corr[analisis][paso];
      this.set(exp, e);
    },
    reiniciar(exp, analisis) { const e = this.get(exp); delete e.dec[analisis]; delete e.corr[analisis]; delete e.tiempos[analisis]; this.set(exp, e); }
  };

  /* ----- resumen del expediente: cuántos puntos cumplen, cuáles faltan y qué recomienda el sistema ----- */
  const TIPOS = [
    { k: 'escrituras',   t: 'Escrituras',                    d: 'Titular, superficie del terreno, identificación', corto: 'Escritura' },
    { k: 'predial',      t: 'Predial',                       d: 'Contribuyente, cuenta o clave predial, superficie', corto: 'Predial' },
    { k: 'alineamiento', t: 'Alineamiento y Número Oficial', d: 'Dirección oficial, número, vigencia, autoridad', corto: 'Alineam.' },
    { k: 'uso',          t: 'Uso de Suelo',                  d: 'Uso autorizado, compatibilidad comercial, restricciones', corto: 'Uso suelo' }
  ];



  /* ----- expedientes reales: se arman con los documentos que ya tenemos, falte lo que falte -----
     analisis/expedientes.json: [{ id, nombre, direccion, busqueda, coords, docs: { escrituras: <id análisis>, predial, alineamiento, uso } }] */
  // compara sin importar mayúsculas, acentos, puntuación ni espacios
  const normalizar = v => String(v == null ? '' : v).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9\/]+/g, ' ').trim();
  // asigna al expediente `exp` los documentos del catálogo `e` (los que falten quedan como faltantes)
  async function asignarDocumentos(exp, e) {
    const idx = await Datos.indice(), docs = {};
    Object.keys(e.docs || {}).forEach(k => { const d = idx.find(x => x.id === e.docs[k]); if (d) docs[k] = { analisis: d.id, archivo: d.archivo }; });
    Estado.set(exp, { docs });
    return docs;
  }

  /* ----- gravedad, reglas y hallazgos ----- */
  const SEV = {
    bloq: { label: 'Bloqueante',  glyph: '!', color: '#B3261E', soft: '#FBE1DD', key: '#F3B8B0', orden: 0 },
    rev:  { label: 'Revisar',     glyph: '?', color: '#B26E00', soft: '#FFF1C2', key: '#FFD966', orden: 1 },
    info: { label: 'Informativo', glyph: 'i', color: '#3B5E8C', soft: '#E3EBF5', key: '#C3D4EA', orden: 2 }
  };
  // reglas del expediente (VC = validación cruzada, ESC = escritura, DOC = calidad del documento)
  const REGLAS = {
    'Calidad del escaneo': { sev: 'bloq', id: 'DOC-01', rule: 'El documento debe ser legible para que los agentes puedan extraer sus datos.', next: 'Solicitar un escaneo nuevo con mayor contraste, o el original.' },
    'Dirección del inmueble': { sev: 'rev', id: 'VC-01', rule: 'La dirección y el número oficial deben coincidir en todo el expediente.', next: 'Solicitar la Constancia de Alineamiento y Número Oficial.', cruza: ['predial', 'alineamiento'] },
    'Libertad de gravamen': { sev: 'rev', id: 'ESC-04', rule: 'El inmueble debe estar libre de gravámenes; se acredita con certificado del Registro Público de la Propiedad con antigüedad máxima de 30 días.', next: 'Solicitar certificado de libertad de gravamen actualizado.' },
    'Superficie del predio': { sev: 'bloq', id: 'VC-03', rule: 'La superficie debe coincidir entre escritura y predial, con tolerancia de ±2 %.', next: 'Solicitar al propietario la aclaración de superficie o la rectificación ante catastro.', cruza: ['predial'] },
    'Titular actual': { sev: 'rev', id: 'VC-02', rule: 'El titular debe coincidir entre la escritura, el predial y los demás documentos.', next: 'Solicitar la boleta de predial o constancia de no adeudo a nombre del titular.', cruza: ['escrituras', 'predial'] },
    'Vigencia': { sev: 'rev', id: 'DOC-03', rule: 'Los documentos con vigencia deben estar vigentes al presentar el expediente.', next: 'Solicitar la renovación del documento vencido.' },
    'Uso de suelo': { sev: 'bloq', id: 'USO-01', rule: 'El uso de suelo debe permitir la operación comercial de la tienda; se acredita con licencia o constancia de uso de suelo.', next: 'Solicitar la licencia o constancia de uso de suelo comercial.' },
    _otro: { sev: 'rev', id: 'DOC-02', rule: 'Todo dato extraído debe poder leerse con claridad en el documento.', next: 'Verificar el dato en el original y corregirlo si hace falta.' }
  };
  const nombreTipo = k => (TIPOS.find(t => t.k === k) || {}).t || k;

  // Convierte los pasos del análisis que quedaron para revisión en hallazgos con gravedad, regla y siguiente paso.
  function hallazgos(an, docs) {
    if (!an) return [];
    const lista = an.pasos.filter(p => !p.ok).map(p => {
      const r = REGLAS[p.campo] || REGLAS._otro;
      const cmp = [[nombreTipo(an.tipo || 'escrituras'), p.valor, p.campo === 'Libertad de gravamen' ? 'warn' : (/No legible/.test(p.valor) ? 'miss' : 'warn')]];
      if (p.campo === 'Libertad de gravamen') cmp[0][1] = 'Declarada por el vendedor en la escritura', cmp.push(['Certificado RPP', 'no está en el expediente', 'miss']);
      (r.cruza || []).forEach(k => cmp.push([nombreTipo(k), docs && docs[k] ? 'recibido: falta contrastar' : 'falta el documento', docs && docs[k] ? 'warn' : 'miss']));
      return { n: p.n, sev: r.sev, titulo: p.campo === 'Calidad del escaneo' ? 'Escaneo con texto casi ilegible' : p.campo === 'Libertad de gravamen' ? 'Libertad de gravamen sin certificado'
        : /No legible/.test(p.valor) ? p.campo + ': no se pudo leer' : p.campo === 'Dirección del inmueble' ? 'Dirección sin contrastar con otros documentos' : p.campo,
        pagina: p.pagina, rect: p.rect, valor: p.valor, compare: cmp, reason: p.nota || 'El agente no pudo confirmar este dato.', ruleId: r.id, rule: r.rule, next: r.next };
    });
    return lista.sort((a, b) => SEV[a.sev].orden - SEV[b.sev].orden || a.n - b.n).map((h, i) => Object.assign(h, { num: String(i + 1).padStart(2, '0') }));
  }

  function hora(ms) {
    const d = new Date(ms), hoy = new Date();
    const h = d.getHours(), m = d.getMinutes(), t = ((h % 12) || 12) + ':' + String(m).padStart(2, '0') + (h < 12 ? ' a. m.' : ' p. m.');
    return (d.toDateString() === hoy.toDateString() ? 'hoy ' : d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' }) + ' ') + t;
  }

  function estadoPaso(paso, dec) {            // lo que vale cada punto tras la verificación humana
    const d = dec && dec[paso.n];
    if (d === 'no') return 'no';
    if (d === 'ok' || d === 'fix') return 'cumple';
    return paso.ok ? 'cumple' : 'pendiente';
  }

  // Resume el expediente con TODOS sus documentos (escritura, predial, alineamiento y uso de suelo), falte lo que falte.
  async function resumen(exp) {
    const e = Estado.get(exp), out = { docs: 0, total: 0, cumple: 0, no: 0, pendientes: 0, hallazgos: [], recomendacion: 'rev', analisis: null, porDoc: {} };
    out.docs = TIPOS.filter(t => e.docs[t.k]).length;
    for (const t of TIPOS) {
      const d = e.docs[t.k]; if (!d || !d.analisis) continue;
      const an = await Datos.analisis(d.analisis), dec = e.dec[d.analisis] || {}, pd = { analisis: an, total: 0, cumple: 0, no: 0, pendientes: 0 };
      if (t.k === 'escrituras') out.analisis = an;
      an.pasos.forEach(p => {
        const s = estadoPaso(p, dec); pd.total++; out.total++;
        if (s === 'cumple') { pd.cumple++; out.cumple++; } else if (s === 'no') { pd.no++; out.no++; } else { pd.pendientes++; out.pendientes++; }
        if (!p.ok || dec[p.n]) out.hallazgos.push({ paso: p, decision: dec[p.n] || null, estado: s, tipo: t.k });
      });
      out.porDoc[t.k] = pd;
    }
    if (!out.analisis) out.analisis = (Object.values(out.porDoc)[0] || {}).analisis || null;
    out.recomendacion = out.no ? 'no' : (out.pendientes || out.docs < 4) ? 'rev' : 'ok';
    return out;
  }

  /* ----- cruce de datos: los mismos datos comparados entre los documentos que haya ----- */
  const CAMPOS_CRUCE = [
    { id: 'titular', label: 'Titular', campo: ['Titular actual', 'Transmitente (vendedor)'] },
    { id: 'direccion', label: 'Dirección', campo: 'Dirección del inmueble' },
    { id: 'superficie', label: 'Superficie', campo: 'Superficie del predio' },
    { id: 'numero', label: 'Número oficial', campo: 'Número oficial' },
    { id: 'cuenta', label: 'Clave catastral', campo: 'Clave catastral' },
    { id: 'predio', label: 'Identificación del predio', campo: 'Identificación del predio' }
  ];
  async function cruce(exp) {
    const e = Estado.get(exp), ans = {};
    for (const t of TIPOS) { const d = e.docs[t.k]; ans[t.k] = d && d.analisis ? await Datos.analisis(d.analisis) : null; }
    const corr = k => ans[k] ? (e.corr[ans[k].id] || {}) : {};
    const paso = (c, k) => { const a = ans[k]; if (!a) return null; for (const n of [].concat(c.campo)) { const p = a.pasos.find(x => x.campo === n); if (p) return p; } return null; };
    const celda = (c, t) => {
      if (!e.docs[t.k]) return { v: null, est: 'falta' };
      if (!ans[t.k]) return { v: null, est: 'cola' };
      const p = paso(c, t.k);
      if (!p && t.k === 'escrituras' && (c.id === 'numero' || c.id === 'predio')) {
        const dp = ans.escrituras.pasos.find(x => x.campo === 'Dirección del inmueble'), tx = dp && (corr('escrituras')[dp.n] || dp.valor), m = tx && tx.match(c.id === 'numero' ? /No\.?\s*([\w\/]+)/i : /Lote\s+\w+,\s*Manzana\s+\w+/i);
        if (m) return { v: c.id === 'numero' ? m[1] : m[0], est: /No legible/.test(tx) ? 'ilegible' : 'ok', p: dp };
      }
      if (!p || /^No consta/.test(p.valor)) return { v: null, est: 'na', p };
      return { v: corr(t.k)[p.n] || p.valor, est: /No legible|Contraste/.test(p.valor) ? 'ilegible' : 'ok', p };
    };
    const resultado = (c, items) => {
      const cs = items.filter(x => x.est === 'ok');
      if (cs.length < 2) return 'pen';
      if (c.id === 'superficie') {
        const n = cs.map(x => parseFloat(String(x.v).replace(/,/g, ''))), mx = Math.max(...n), mn = Math.min(...n);
        if (n.every(isFinite)) return (mx - mn) / mx <= 0.02 ? 'ok' : 'dif';
      }
      let vs = cs.map(x => normalizar(x.v));
      if (c.id === 'cuenta') vs = vs.map(v => v.replace(/\s+/g, ''));
      const mismo = c.id === 'numero' || c.id === 'cuenta' ? (a, b) => a === b : (a, b) => a === b || a.includes(b) || b.includes(a);
      return vs.every(a => vs.every(b => mismo(a, b))) ? 'ok' : 'dif';
    };
    const campos = CAMPOS_CRUCE.map(c => {
      const items = TIPOS.map(t => Object.assign({ k: t.k, doc: t.t, corto: t.corto }, celda(c, t)));
      const grupos = [];
      items.filter(x => x.est === 'ok').forEach(x => { const k = normalizar(x.v), g = grupos.find(y => y.k === k); if (g) g.docs.push(x.corto); else grupos.push({ k, v: x.v, docs: [x.corto] }); });
      return Object.assign({}, c, { items, grupos, res: resultado(c, items) });
    });
    return { ans, campos, docs: e.docs };
  }

  /* ----- barra lateral, igual en todas las pantallas ----- */
  const IC = {
    tiendas: '<path d="M3 9l1.5-5h15L21 9M3 9h18M3 9v2a3 3 0 006 0 3 3 0 006 0 3 3 0 006 0V9M5 13v7h14v-7M10 20v-4h4v4"/>',
    expedientes: '<path d="M9 4h6v3H9zM7 5H5v16h14V5h-2M8 12h8M8 16h5"/>',
    validacion: '<path d="M4 5h6v14H4zM14 5h6v14h-6M10 9h4M10 15h4"/>'
  };
  const svg = p => `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
  const hrefMapa = exp => 'index.html?sinintro=1' + (exp ? '&zona=' + encodeURIComponent(exp) : '');
  function rail(activo) {
    const exp = new URLSearchParams(location.search).get('exp'), q = exp ? '?exp=' + encodeURIComponent(exp) : '';
    const item = (k, titulo, href) => activo === k
      ? `<button class="ic on" aria-label="${titulo}" aria-current="page">${svg(IC[k])}<span class="lb">${titulo}</span></button>`
      : `<a class="ic" href="${href}" aria-label="${titulo}" title="${titulo}">${svg(IC[k])}<span class="lb">${titulo}</span></a>`;
    return `<div class="logo">3B</div>${item('tiendas', 'Mapa', hrefMapa(exp))}${item('expedientes', 'Documentos', 'analizador.html' + q)}${item('validacion', 'Cruce', 'validacion.html' + q)}`;
  }
  // selector de vista del mismo expediente: Documentos · Cruce de datos · Agentes
  function nav(activo, exp, docId) {
    const q = exp ? '?exp=' + encodeURIComponent(exp) : '';
    const it = (k, t, href) => k === activo ? `<span class="on" aria-current="page">${t}</span>` : `<a href="${href}">${t}</a>`;
    return `<div class="seg2" role="navigation" aria-label="Vistas del expediente">${it('docs', 'Documentos', 'analizador.html' + q)}${it('cruce', 'Cruce de datos', 'validacion.html' + q)}${it('agentes', 'Agentes', 'revision.html' + q + (docId ? (q ? '&' : '?') + 'doc=' + encodeURIComponent(docId) : ''))}</div>`;
  }

  const escapar = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const parametros = () => new URLSearchParams(location.search);

  window.Modulo = { Datos, Estado, recibir, normalizar, asignarDocumentos, cruce, nav, hrefMapa, TIPOS, SEV, REGLAS, hallazgos, hora, nombreTipo, estadoPaso, resumen, rail, escapar, parametros };
})();
