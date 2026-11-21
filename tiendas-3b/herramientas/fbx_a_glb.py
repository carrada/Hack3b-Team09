"""Convierte una malla (LOD) de un FBX binario a GLB para Mapbox: base en y = 0, centrada, lado largo = LARGO metros.
Uso: python3 -I fbx_a_glb.py <modelo.fbx> <lod 0-4> <difusa.jpg> <normal.jpg> <salida.glb> [largo_m]"""
import sys, os, json, struct, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fbxlib

fbx, lod, dif, nor, salida = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
LARGO = float(sys.argv[6]) if len(sys.argv) > 6 else 60.0
_, raiz = fbxlib.leer(fbx)
obj = next(r for r in raiz if r['n'] == 'Objects')
g = fbxlib.hijos(obj, 'Geometry')[lod]
V = fbxlib.hijo(g, 'Vertices')['p'][0]
PV = fbxlib.hijo(g, 'PolygonVertexIndex')['p'][0]
ln = fbxlib.hijo(g, 'LayerElementNormal'); lu = fbxlib.hijo(g, 'LayerElementUV')
N = fbxlib.hijo(ln, 'Normals')['p'][0]; NI = fbxlib.hijo(ln, 'NormalsIndex')['p'][0]
U = fbxlib.hijo(lu, 'UV')['p'][0]; UI = fbxlib.hijo(lu, 'UVIndex')['p'][0]

# polígonos -> triángulos (abanico); cada esquina = (vértice, índice de normal, índice de uv)
esquinas, tris, poli = [], [], []
for k, i in enumerate(PV):
    v = ~i if i < 0 else i
    poli.append((v, NI[k], UI[k]))
    if i < 0:
        for j in range(1, len(poli) - 1): tris.append((poli[0], poli[j], poli[j + 1]))
        poli = []
mapa, pos, nrm, uvs, idx = {}, [], [], [], []
# Z arriba (FBX/Blender) -> Y arriba (glTF): (x, y, z) -> (x, z, -y)
for t in tris:
    for c in t:
        if c not in mapa:
            mapa[c] = len(pos)
            x, y, z = V[c[0]*3:c[0]*3+3]; pos.append((x, z, -y))
            x, y, z = N[c[1]*3:c[1]*3+3]; nrm.append((x, z, -y))
            uvs.append((U[c[2]*2], 1 - U[c[2]*2+1]))
        idx.append(mapa[c])
xs = [p[0] for p in pos]; ys = [p[1] for p in pos]; zs = [p[2] for p in pos]
cx, cz, y0 = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2, min(ys)
lado = max(max(xs) - min(xs), max(zs) - min(zs)); k = LARGO / lado
pos = [((x - cx) * k, (y - y0) * k, (z - cz) * k) for x, y, z in pos]
mn = [min(p[i] for p in pos) for i in range(3)]; mx = [max(p[i] for p in pos) for i in range(3)]

bin_ = bytearray()
def vista(datos, destino=None):
    while len(bin_) % 4: bin_.append(0)
    ini = len(bin_); bin_.extend(datos); return {'buffer': 0, 'byteOffset': ini, 'byteLength': len(datos), **({'target': destino} if destino else {})}
vistas = []
vistas.append(vista(b''.join(struct.pack('<3f', *p) for p in pos), 34962))
vistas.append(vista(b''.join(struct.pack('<3f', *p) for p in nrm), 34962))
vistas.append(vista(b''.join(struct.pack('<2f', *p) for p in uvs), 34962))
ancho = 'I' if len(pos) > 65535 else 'H'
vistas.append(vista(struct.pack('<%d%s' % (len(idx), ancho), *idx), 34963))
for ruta in (dif, nor): vistas.append(vista(open(ruta, 'rb').read()))
gltf = {
  'asset': {'version': '2.0', 'generator': 'fbx_a_glb.py'},
  'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'centro_distribucion'}],
  'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3, 'material': 0}]}],
  'materials': [{'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0.0, 'roughnessFactor': 0.85}, 'normalTexture': {'index': 1}}],
  'textures': [{'source': 0, 'sampler': 0}, {'source': 1, 'sampler': 0}], 'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}],
  'images': [{'bufferView': 4, 'mimeType': 'image/jpeg'}, {'bufferView': 5, 'mimeType': 'image/jpeg'}],
  'accessors': [
    {'bufferView': 0, 'componentType': 5126, 'count': len(pos), 'type': 'VEC3', 'min': mn, 'max': mx},
    {'bufferView': 1, 'componentType': 5126, 'count': len(nrm), 'type': 'VEC3'},
    {'bufferView': 2, 'componentType': 5126, 'count': len(uvs), 'type': 'VEC2'},
    {'bufferView': 3, 'componentType': 5125 if ancho == 'I' else 5123, 'count': len(idx), 'type': 'SCALAR'}],
  'bufferViews': vistas, 'buffers': [{'byteLength': len(bin_)}]}
js = json.dumps(gltf, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
while len(bin_) % 4: bin_.append(0)
out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<I4s', len(js), b'JSON') + js + struct.pack('<I4s', len(bin_), b'BIN\0') + bytes(bin_)
open(salida, 'wb').write(out)
print('triángulos', len(idx) // 3, 'vértices', len(pos), 'tamaño', len(out) // 1024, 'KB', 'caja (m)', [round(b - a, 1) for a, b in zip(mn, mx)])
