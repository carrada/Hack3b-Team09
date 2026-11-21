"""Herramientas deterministas compartidas (código, NO LLM).

Se exponen como `@tool` de LangChain (registro HERRAMIENTAS) y los agentes las
invocan con `usar(nombre, **kwargs)`, que además deja rastro en la bitácora.
"""
from __future__ import annotations

import re
import threading
from datetime import date, timedelta
from typing import Optional

from dateutil.relativedelta import relativedelta
from langchain_core.tools import tool
from rapidfuzz import fuzz
from unidecode import unidecode

from .config import DIR_KB

# =================================================================== texto


def norm(s: Optional[str]) -> str:
    """minúsculas, sin acentos, sin puntuación, espacios colapsados."""
    if not s:
        return ""
    s = unidecode(str(s)).lower()
    s = re.sub(r"[^a-z0-9#&/\- ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_ABREV_DIR = [
    (r"\bav(da)?\b", "avenida"), (r"\bblvd?\b", "boulevard"), (r"\bbulevar(d)?\b", "boulevard"),
    (r"\bcalz\b", "calzada"), (r"\bc\b(?= [a-z])", "calle"), (r"\bcol\b", "colonia"),
    (r"\bfracc?\b", "fraccionamiento"), (r"\bcarr\b", "carretera"), (r"\bprol\b", "prolongacion"),
    (r"\bmpio\b", "municipio"), (r"\bedo\b", "estado"), (r"\bmz(a)?\b", "manzana"), (r"\blt\b", "lote"),
    (r"\bpriv\b", "privada"), (r"\bkm\b", "kilometro"), (r"\bsta\b", "santa"),
]
_RUIDO_DIR = r"\b(numero|num|no|n|ext|exterior|oficial|interior|int|cp|c p|codigo postal|domicilio|ubicado en|ubicacion|predio|inmueble|sin numero)\b"


@tool
def normalizar_direccion(direccion: str) -> str:
    """Normaliza una dirección mexicana: abreviaturas, acentos, '#', 'No.', etc."""
    s = norm(direccion).replace("#", " ")
    for patron, rep in _ABREV_DIR:
        s = re.sub(patron, rep, s)
    s = re.sub(_RUIDO_DIR, " ", s)
    return re.sub(r"\s+", " ", s).strip()


_TITULOS = r"\b(c|ciudadano|ciudadana|sr|sra|srita|senor|senora|lic|licenciado|licenciada|ing|ingeniero|arq|dr|dra|don|dona|la|el|los|sucesion|de la|del)\b"
_SOCIEDADES = [
    (r"\bs\s*a\s*p\s*i\s*de\s*c\s*v\b", "sapi de cv"), (r"\bs\s*a\s*de\s*c\s*v\b", "sa de cv"),
    (r"\bs\s*de\s*r\s*l\s*de\s*c\s*v\b", "s de rl de cv"), (r"\bs\s*de\s*r\s*l\b", "s de rl"),
    (r"\bs\s*c\b", "sc"), (r"\ba\s*c\b", "ac"),
]


@tool
def normalizar_nombre(nombre: str) -> str:
    """Normaliza nombres de personas físicas o morales (títulos, 'S.A. de C.V.', acentos)."""
    s = norm(nombre).replace("-", " ")
    for patron, rep in _SOCIEDADES:
        s = re.sub(patron, rep, s)
    s = re.sub(_TITULOS, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def similitud(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return float(max(fuzz.token_sort_ratio(a, b), fuzz.token_set_ratio(a, b) * 0.97))


@tool
def comparar_direcciones(a: str, b: str) -> float:
    """Score 0-100 de similitud entre dos direcciones (normalizadas)."""
    na, nb = normalizar_direccion.invoke(a), normalizar_direccion.invoke(b)
    score = similitud(na, nb)
    # si los números exteriores difieren claramente, castiga
    num_a, num_b = numero_oficial_normalizado(a), numero_oficial_normalizado(b)
    if num_a and num_b and num_a != num_b and num_a.rstrip("abcdefgh") != num_b.rstrip("abcdefgh"):
        score = min(score, 70.0)
    return round(score, 1)


@tool
def comparar_nombres(a: str, b: str) -> float:
    """Score 0-100 de similitud entre dos nombres (orden de apellidos indiferente)."""
    return round(similitud(normalizar_nombre.invoke(a), normalizar_nombre.invoke(b)), 1)


def numero_oficial_normalizado(s: Optional[str]) -> str:
    """'#12-A' -> '12a', 'No. 1520' -> '1520', 'S/N' -> 'sn'."""
    if not s:
        return ""
    t = norm(s)
    if re.search(r"\bs\s*/?\s*n\b|sin numero", t):
        return "sn"
    m = re.search(r"(\d{1,6})\s*-?\s*([a-h])?\b", t)
    if not m:
        return ""
    return m.group(1).lstrip("0") + (m.group(2) or "")


def clave_normalizada(s: Optional[str]) -> str:
    return re.sub(r"[^0-9a-z]", "", norm(s))


# =================================================================== superficies

def parse_superficie(s: Optional[str]) -> Optional[float]:
    """Convierte '1,234.56 m2', '1.234,56 m²', '2.5 ha', '0-45-20 has' a m²."""
    if not s:
        return None
    t = unidecode(str(s)).lower()
    m = re.search(r"(\d{1,3})-(\d{2})-(\d{2}(?:\.\d+)?)\s*(has?|hectareas)", t)
    if m:  # hectáreas-áreas-centiáreas
        return int(m.group(1)) * 10000 + int(m.group(2)) * 100 + float(m.group(3))
    m = re.search(r"(\d[\d.,\s]*\d|\d)", t)
    if not m:
        return None
    num = m.group(1).replace(" ", "")
    if "," in num and "." in num:
        num = num.replace(",", "") if num.rfind(".") > num.rfind(",") else num.replace(".", "").replace(",", ".")
    elif "," in num:
        partes = num.split(",")
        num = num.replace(",", "") if len(partes[-1]) == 3 else num.replace(",", ".")
    elif num.count(".") > 1:
        num = num.replace(".", "")
    try:
        valor = float(num)
    except ValueError:
        return None
    resto = t[m.end():m.end() + 25]
    if re.match(r"\s*(ha|has|hectareas?)\b", resto):
        valor *= 10000
    return valor


@tool
def comparar_superficies(a: str, b: str, tolerancia: float = 0.05) -> dict:
    """Compara dos superficies (texto con unidad). Devuelve m², diferencia relativa y si está dentro de tolerancia."""
    va, vb = parse_superficie(a), parse_superficie(b)
    if va is None or vb is None or max(va, vb) == 0:
        return {"comparable": False, "a_m2": va, "b_m2": vb}
    dif = abs(va - vb) / max(va, vb)
    return {"comparable": True, "a_m2": va, "b_m2": vb, "diferencia_rel": round(dif, 4), "dentro_tolerancia": dif <= tolerancia}


# =================================================================== fechas y vigencia

_MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
     "septiembre", "octubre", "noviembre", "diciembre"], start=1)}
_MESES.update({"setiembre": 9})
_MESES_CORTOS = {k[:3]: v for k, v in _MESES.items()}

_NUM_PAL = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
            "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "dieciocho": 18,
            "veinticuatro": 24, "treinta": 30, "sesenta": 60, "noventa": 90, "ciento ochenta": 180}


def parse_fecha(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    t = unidecode(str(s)).lower().strip()
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{2,4})", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        try:
            return date(y, mo, d)
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})[\s\-/]*(?:de\s+)?([a-z]{3,10})\.?[\s\-/]*(?:de(?:l)?\s+)?(\d{4})", t)
    if m:
        mes = _MESES.get(m.group(2)) or _MESES_CORTOS.get(m.group(2)[:3])
        if mes:
            try:
                return date(int(m.group(3)), mes, int(m.group(1)))
            except ValueError:
                pass
    m = re.search(r"([a-z]{3,10})\s+(\d{1,2}),?\s+(?:de\s+)?(\d{4})", t)
    if m:
        mes = _MESES.get(m.group(1)) or _MESES_CORTOS.get(m.group(1)[:3])
        if mes:
            try:
                return date(int(m.group(3)), mes, int(m.group(2)))
            except ValueError:
                pass
    return None


def _plazo(texto: str) -> Optional[relativedelta]:
    t = unidecode(texto).lower()
    for pal, n in sorted(_NUM_PAL.items(), key=lambda x: -len(x[0])):
        t = re.sub(rf"\b{pal}\b", str(n), t)
    m = re.search(r"(\d+)\s*(anos?|años?|meses?|mes|dias?|días?)", t)
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    if u.startswith("an") or u.startswith("añ"):
        return relativedelta(years=n)
    if u.startswith("mes"):
        return relativedelta(months=n)
    return relativedelta(days=n)


@tool
def calcular_vigencia(fecha_emision: Optional[str], vigencia: Optional[str], fecha_ref: str,
                      dias_alerta: int = 30, vigencia_default_dias: Optional[int] = None) -> dict:
    """Determina si un documento está vigente. Estados: vigente | por_vencer | vencido | sin_vencimiento | indeterminable."""
    ref = date.fromisoformat(fecha_ref)
    emision = parse_fecha(fecha_emision)
    v = unidecode(vigencia or "").lower()
    if re.search(r"indefinid|permanente|sin vigencia|no caduca|sin fecha de vencimiento|hasta en tanto", v):
        return {"estado": "sin_vencimiento", "vence": None, "emision": str(emision) if emision else None}
    vence = None
    if v:
        vence = parse_fecha(v) if re.search(r"\d{4}", v) and not re.search(r"\d+\s*(anos?|años?|mes|dias?)", v) else None
        if vence is None and emision:
            p = _plazo(v)
            if p:
                vence = emision + p
    if vence is None and emision and vigencia_default_dias:
        vence = emision + timedelta(days=int(vigencia_default_dias))
    if vence is None:
        return {"estado": "indeterminable", "vence": None, "emision": str(emision) if emision else None}
    dias = (vence - ref).days
    estado = "vencido" if dias < 0 else ("por_vencer" if dias <= dias_alerta else "vigente")
    return {"estado": estado, "vence": str(vence), "dias_restantes": dias, "emision": str(emision) if emision else None}


# =================================================================== CURP / RFC

_CURP_RE = re.compile(r"^[A-Z][AEIOUX][A-Z]{2}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[HMX]"
                      r"(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)"
                      r"[B-DF-HJ-NP-TV-Z]{3}[0-9A-Z]\d$")
_CURP_DICC = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"


def digito_curp(curp17: str) -> str:
    suma = sum(_CURP_DICC.index(c) * (18 - i) for i, c in enumerate(curp17))
    return str((10 - suma % 10) % 10)


@tool
def validar_curp(curp: str) -> dict:
    """Valida formato y dígito verificador de una CURP."""
    c = re.sub(r"[\s\-]", "", (curp or "").upper())
    if len(c) != 18:
        return {"valida": False, "motivo": f"longitud {len(c)} (se esperan 18)", "valor": c}
    if not _CURP_RE.match(c):
        return {"valida": False, "motivo": "formato inválido", "valor": c}
    if digito_curp(c[:17]) != c[17]:
        return {"valida": False, "motivo": "dígito verificador no coincide (posible error de OCR)", "valor": c}
    return {"valida": True, "motivo": "formato y dígito verificador correctos", "valor": c}


_RFC_RE = re.compile(r"^([A-ZÑ&]{3,4})(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([A-Z\d]{2})([A\d])$")
_RFC_DICC = "0123456789ABCDEFGHIJKLMN&OPQRSTUVWXYZ Ñ"


def digito_rfc(rfc_sin_dv: str) -> str:
    base = rfc_sin_dv.rjust(12, " ")
    suma = sum(_RFC_DICC.index(c) * (13 - i) for i, c in enumerate(base))
    r = suma % 11
    if r == 0:
        return "0"
    d = 11 - r
    return "A" if d == 10 else str(d)


@tool
def validar_rfc(rfc: str) -> dict:
    """Valida formato y homoclave/dígito verificador de un RFC (13 = persona física, 12 = persona moral)."""
    r = re.sub(r"[\s\-]", "", (rfc or "").upper())
    if len(r) not in (12, 13):
        return {"valida": False, "motivo": f"longitud {len(r)} (se esperan 12 o 13)", "valor": r}
    if not _RFC_RE.match(r):
        return {"valida": False, "motivo": "formato inválido", "valor": r}
    tipo = "moral" if len(r) == 12 else "fisica"
    if digito_rfc(r[:-1]) != r[-1]:
        return {"valida": False, "motivo": "dígito verificador no coincide (posible error de OCR)", "valor": r, "persona": tipo}
    return {"valida": True, "motivo": "formato y dígito verificador correctos", "valor": r, "persona": tipo}


_A_DIGITO = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6", "T": "7"})
_A_LETRA = str.maketrans({"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G"})


def corregir_ocr_id(valor: str) -> Optional[str]:
    """Corrige confusiones típicas del OCR (O↔0, I↔1, S↔5…) según la posición en RFC/CURP.
    Devuelve el valor corregido solo si queda válido; None si no hay corrección posible."""
    v = re.sub(r"[\s\-]", "", (valor or "").upper())
    if len(v) == 18:  # CURP: 4 letras, 6 dígitos, 6 letras, 1 alfanum, 1 dígito
        c = v[:4].translate(_A_LETRA) + v[4:10].translate(_A_DIGITO) + v[10:16].translate(_A_LETRA) + v[16] + v[17].translate(_A_DIGITO)
        return c if c != v and validar_curp.invoke({"curp": c})["valida"] else None
    if len(v) in (12, 13):
        n = len(v) - 9  # letras iniciales: 3 (moral) o 4 (física)
        c = v[:n].translate(_A_LETRA) + v[n:n + 6].translate(_A_DIGITO) + v[n + 6:]
        return c if c != v and validar_rfc.invoke({"rfc": c})["valida"] else None
    return None


def identificadores_en(texto: str) -> list[tuple[str, str]]:
    """Busca tokens con forma de CURP (18) o RFC (12/13). Devuelve [(tipo, valor)]."""
    t = (texto or "").upper()
    salida = []
    for tok in re.findall(r"\b[A-ZÑ&0-9]{12,18}\b", t):
        if len(tok) == 18 and re.match(r"^[A-Z]{4}\d{6}", tok):
            salida.append(("CURP", tok))
        elif len(tok) in (12, 13) and re.match(r"^[A-ZÑ&]{3,4}\d{6}", tok):
            salida.append(("RFC", tok))
    return salida


# =================================================================== citas

@tool
def verificar_cita(texto_pagina: str, fragmento: str) -> float:
    """Score 0-100: qué tan literalmente aparece `fragmento` en el texto OCR de la página."""
    a, b = norm(fragmento), norm(texto_pagina)
    if not a or not b:
        return 0.0
    if a in b:
        return 100.0
    if len(a) > len(b):
        return float(fuzz.ratio(a, b))
    return float(fuzz.partial_ratio(a, b))


# =================================================================== base de conocimiento

_KB_LOCK = threading.Lock()


def _leer_kb_raw(tipo: str) -> tuple[list[str], list[str]]:
    ruta = DIR_KB / f"{tipo}.md"
    if not ruta.exists():
        return [], []
    conf, pend, seccion = [], [], None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion = "c" if "confirm" in linea.lower() else ("p" if "pendiente" in linea.lower() else None)
        elif linea.startswith("- ") and seccion:
            entrada = linea[2:].split(" ⟵ ")[0].strip()
            (conf if seccion == "c" else pend).append(entrada)
    return conf, pend


@tool
def leer_kb(tipo: str) -> dict:
    """Lee la base de conocimiento MD de un especialista: entradas confirmadas y pendientes."""
    c, p = _leer_kb_raw(tipo)
    return {"confirmadas": c, "pendientes": p}


def sanitizar_entrada_kb(valor: str) -> str:
    """Sin datos personales: de una notaría solo se guarda 'Notaría Pública N'; de autoridades, el nombre de la dependencia."""
    v = re.sub(r"\s+", " ", valor or "").strip()
    m = re.search(r"notar[ií]a(?:\s+p[uú]blica)?\s*(?:n[uú]m(?:ero)?\.?|no\.?|#|n°)?\s*\d+", v, re.I)
    if m:
        return m.group(0).strip()
    v = re.split(r",\s*(?:lic|ing|arq|c\.|dr)\b|\b(?:lic|ing|arq)\.\s", v, flags=re.I)[0]
    return v[:120].strip(" ,.;")


def buscar_kb(tipo: str, valor: str) -> str:
    """'confirmada' | 'pendiente' | 'generica' (coincide con una categoría) | 'desconocida'."""
    conf, pend = _leer_kb_raw(tipo)
    nv = norm(sanitizar_entrada_kb(valor))
    if not nv:
        return "desconocida"
    for e in conf:
        if fuzz.ratio(nv, norm(e)) >= 90:
            return "confirmada"
    for e in pend:
        if fuzz.ratio(nv, norm(e)) >= 90:
            return "pendiente"
    for e in conf:
        if norm(e) in nv or fuzz.token_set_ratio(nv, norm(e)) >= 90:
            return "generica"
    return "desconocida"


@tool
def proponer_alta_kb(tipo: str, entrada: str, fuente: str) -> str:
    """Agrega una entrada a la sección 'Pendientes' del MD de conocimiento (requiere confirmación humana)."""
    limpia = sanitizar_entrada_kb(entrada)
    if not limpia:
        return "vacía"
    with _KB_LOCK:
        conf, pend = _leer_kb_raw(tipo)
        if any(fuzz.ratio(norm(limpia), norm(e)) >= 90 for e in conf + pend):
            return "ya existe"
        ruta = DIR_KB / f"{tipo}.md"
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(f"- {limpia} ⟵ propuesta automática ({date.today()}, doc {fuente})\n")
    return "pendiente"


# =================================================================== registro

HERRAMIENTAS = {t.name: t for t in [
    validar_curp, validar_rfc, normalizar_direccion, normalizar_nombre, comparar_direcciones,
    comparar_nombres, comparar_superficies, calcular_vigencia, verificar_cita, leer_kb, proponer_alta_kb,
]}


def usar(nombre: str, bitacora: list[str] | None = None, **kwargs):
    """Invoca una herramienta del registro y deja rastro en la bitácora."""
    res = HERRAMIENTAS[nombre].invoke(kwargs)
    if bitacora is not None:
        args = ", ".join(f"{k}={str(v)[:40]!r}" for k, v in kwargs.items() if k != "texto_pagina")
        bitacora.append(f"🔧 {nombre}({args}) → {str(res)[:80]}")
    return res
