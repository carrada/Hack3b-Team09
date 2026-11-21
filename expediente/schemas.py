"""Esquemas Pydantic compartidos por todos los agentes.

La evidencia es parte del esquema: cada campo y cada hallazgo apuntan a
documento + página + fragmento literal, que el Dictamen verifica contra el OCR.
"""
from __future__ import annotations

import operator
from typing import Annotated, Literal, Optional, TypedDict

from pydantic import BaseModel, Field

Estado = Literal["cumple", "requiere_revision", "no_cumple"]
TipoDoc = Literal["escrituras", "predial", "alineamiento", "uso_suelo"]

ICONO = {"cumple": "✅", "requiere_revision": "⚠️", "no_cumple": "❌"}
ETIQUETA = {"cumple": "Cumple", "requiere_revision": "Requiere revisión", "no_cumple": "No cumple"}
ORDEN = {"cumple": 0, "requiere_revision": 1, "no_cumple": 2}


def peor(*estados: str) -> str:
    return max(estados, key=lambda e: ORDEN[e]) if estados else "cumple"


# ---------------------------------------------------------------- documentos
class Pagina(BaseModel):
    numero: int
    texto: str
    fuente: Literal["nativo", "ocr"] = "nativo"
    calidad: float = 1.0  # 0-1 (confianza media de Tesseract o 1.0 si es texto nativo)


class Documento(BaseModel):
    id: str
    nombre_archivo: str
    ruta: str
    sha256: str
    paginas: list[Pagina] = []
    tipo: Optional[str] = None            # escrituras | predial | alineamiento | uso_suelo | None
    tipo_metodo: str = ""                 # palabras_clave | llm
    tipo_confianza: float = 0.0
    descartado: bool = False
    motivo_descarte: str = ""
    huella: dict[str, Optional[str]] = {}  # direccion / propietario / clave_catastral (para agrupar)
    grupo: Optional[int] = None

    @property
    def calidad(self) -> float:
        if not self.paginas:
            return 0.0
        return sum(p.calidad for p in self.paginas) / len(self.paginas)

    def texto_con_paginas(self, max_chars: int | None = None) -> str:
        partes = [f"=== PÁGINA {p.numero} ===\n{p.texto}" for p in self.paginas]
        txt = "\n\n".join(partes)
        if max_chars and len(txt) > max_chars:
            mitad = max_chars // 2
            txt = txt[:mitad] + "\n\n[... texto omitido por longitud ...]\n\n" + txt[-mitad:]
        return txt


# ---------------------------------------------------------------- evidencia
class Evidencia(BaseModel):
    documento_id: str
    pagina: int
    fragmento: str             # texto literal del OCR
    verificada: bool = False   # la llena el Dictamen
    score_verificacion: float = 0.0


class Campo(BaseModel):
    nombre: str
    valor: Optional[str] = None
    evidencia: Optional[Evidencia] = None
    confianza: float = 0.0     # 0-1


class Hallazgo(BaseModel):
    regla_id: str
    documento_id: str = ""
    severidad: Literal["critica", "menor", "info"]
    resultado: Estado
    descripcion: str
    evidencias: list[Evidencia] = []


class ResultadoDocumento(BaseModel):
    documento_id: str
    nombre_archivo: str
    tipo: TipoDoc
    agente: str
    campos: list[Campo]
    hallazgos: list[Hallazgo]
    estado: Estado
    motivos: list[str]
    reglas_evaluadas: int = 0
    reglas_pasan: int = 0
    obligatorios_total: int = 0
    obligatorios_encontrados: int = 0
    calidad_ocr: float = 1.0
    error: Optional[str] = None

    def campo(self, nombre: str) -> Optional[Campo]:
        for c in self.campos:
            if c.nombre == nombre and c.valor:
                return c
        return None


class Cruce(BaseModel):
    """Una comparación realizada por el Validador cruzado (coincida o no)."""
    atributo: str
    valores: dict[str, str]          # documento_id -> valor
    score: float                     # 0-100
    resultado: Literal["coincide", "difiere", "ambiguo"]
    metodo: Literal["exacto", "fuzzy", "numerico", "llm"]
    explicacion: str = ""


class Discrepancia(BaseModel):
    atributo: Literal["direccion", "propietario", "superficie", "numero_oficial",
                      "id_predio", "otro_inmueble", "faltante"]
    valores: dict[str, str]
    evidencias: list[Evidencia] = []
    severidad: Literal["critica", "menor"]
    explicacion: str


class Dictamen(BaseModel):
    recomendacion: Estado
    confianza: int
    senales_confianza: dict[str, float]
    uso_requerido: str
    documentos_recibidos: list[str]
    documentos_faltantes: list[str]
    documentos_descartados: list[str]
    requisitos_cumplidos: list[str]
    requisitos_no_cumplidos: list[str]
    discrepancias: list[Discrepancia]
    razones: list[str]
    resumen: str = ""
    requiere_humano: bool
    puntos_a_verificar: list[str]
    citas_total: int = 0
    citas_verificadas: int = 0


# ---------------------------------------------------------------- estado del grafo
class ExpedienteState(TypedDict, total=False):
    """Estado compartido. Se guardan dicts (model_dump) para que el checkpointer serialice sin sorpresas."""
    uso_requerido: str                 # tienda | cedis
    hitl: bool                         # activar human in the loop (interrupt)
    archivos: list[str]
    resultados_verificados: list[dict]  # ResultadoDocumento con citas verificadas por el Dictamen
    documentos: list[dict]             # Documento aceptados
    descartados: list[dict]            # Documento descartados
    resultados: Annotated[list[dict], operator.add]   # ResultadoDocumento (fan-in de especialistas)
    cruces: list[dict]                 # Cruce
    discrepancias: list[dict]          # Discrepancia
    dictamen: dict                     # Dictamen
    revision_humana: dict
    bitacora: Annotated[list[str], operator.add]


class EnvioEspecialista(TypedDict):
    """Payload que el fan-out (Send) entrega a cada especialista."""
    tipo: str
    documentos: list[dict]
    uso_requerido: str


# ---------------------------------------------------------------- salidas LLM
class CampoLLM(BaseModel):
    nombre: str = Field(description="Nombre exacto del campo solicitado")
    valor: Optional[str] = Field(None, description="Valor normalizado legible; null si no aparece en el documento")
    pagina: Optional[int] = Field(None, description="Número de página donde aparece (según los marcadores === PÁGINA n ===)")
    fragmento: Optional[str] = Field(None, description="Copia LITERAL y breve (10-200 caracteres) del texto del documento que sustenta el valor, sin corregir errores de OCR")


class ExtraccionLLM(BaseModel):
    campos: list[CampoLLM]
    observaciones: list[str] = Field(default_factory=list, description="Riesgos o anomalías notables vistas en el documento (tachaduras, ilegibilidad, sellos faltantes, documento de otro inmueble, etc.)")


class ClasificacionLLM(BaseModel):
    tipo: Literal["escrituras", "predial", "alineamiento", "uso_suelo", "otro"]
    es_documento_legal: bool = Field(description="False si es foto, identificación suelta (INE/CURP), basura o algo no relacionado")
    motivo: str
    direccion: Optional[str] = Field(None, description="Dirección del inmueble si aparece")
    propietario: Optional[str] = Field(None, description="Propietario/titular/contribuyente si aparece")
    clave_catastral: Optional[str] = Field(None, description="Clave catastral o cuenta predial si aparece")


class JuicioLLM(BaseModel):
    resultado: Estado = Field(description="cumple / requiere_revision / no_cumple")
    explicacion: str
    pagina: Optional[int] = None
    fragmento: Optional[str] = Field(None, description="Cita LITERAL breve del documento que sustenta el juicio")


class MismoInmuebleLLM(BaseModel):
    mismo: bool
    explicacion: str
