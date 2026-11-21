"""Lector mínimo de FBX binario (solo lo necesario para sacar mallas). Sin dependencias."""
import struct, zlib

def leer(ruta):
    d = open(ruta, 'rb').read()
    assert d[:20] == b'Kaydara FBX Binary  ', 'no es un FBX binario'
    ver = struct.unpack('<I', d[23:27])[0]
    big = ver >= 7500
    pos = 27
    def nodo(pos):
        if big: end, nprops, plen, nl = struct.unpack('<QQQB', d[pos:pos+25]); pos += 25
        else: end, nprops, plen, nl = struct.unpack('<IIIB', d[pos:pos+13]); pos += 13
        if end == 0: return None, pos
        name = d[pos:pos+nl].decode('latin1'); pos += nl
        props = []
        for _ in range(nprops):
            t = chr(d[pos]); pos += 1
            if t in 'YCIFDL':
                fmt = {'Y': '<h', 'C': '<?', 'I': '<i', 'F': '<f', 'D': '<d', 'L': '<q'}[t]
                props.append(struct.unpack_from(fmt, d, pos)[0]); pos += struct.calcsize(fmt)
            elif t in 'fdlib':
                n, enc, clen = struct.unpack_from('<III', d, pos); pos += 12
                raw = d[pos:pos+clen]; pos += clen
                if enc: raw = zlib.decompress(raw)
                code = {'f': 'f', 'd': 'd', 'l': 'q', 'i': 'i', 'b': 'b'}[t]
                props.append(struct.unpack('<%d%s' % (n, code), raw))
            elif t in 'SR':
                n = struct.unpack_from('<I', d, pos)[0]; pos += 4
                raw = d[pos:pos+n]; pos += n
                props.append(raw if t == 'R' else raw.decode('utf8', 'replace'))
            else: raise ValueError('tipo ' + t)
        hijos = []
        while pos < end:
            h, pos = nodo(pos)
            if h is None: break
            hijos.append(h)
        return {'n': name, 'p': props, 'c': hijos}, end
    raiz = []
    while pos < len(d) - 160:
        h, pos = nodo(pos)
        if h is None: break
        raiz.append(h)
    return ver, raiz

def hijo(n, nombre): return next((h for h in n['c'] if h['n'] == nombre), None)
def hijos(n, nombre): return [h for h in n['c'] if h['n'] == nombre]
