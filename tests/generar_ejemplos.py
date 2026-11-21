"""Genera expedientes SINTÉTICOS (datos ficticios) para probar el flujo sin usar documentos del reto.

  ejemplos/ok/          4 documentos consistentes (la escritura va como imagen escaneada → OCR)
  ejemplos/problemas/   predial a nombre de otra persona, número oficial distinto, uso habitacional,
                        un predial de OTRO inmueble y un archivo basura
"""
from pathlib import Path

import pymupdf as fitz

from expediente.tools import digito_rfc

RAIZ = Path(__file__).resolve().parent.parent / "ejemplos"
RFC = "IDN050310AB"
RFC = RFC + digito_rfc(RFC)

ESCRITURA = f"""ESCRITURA PÚBLICA NÚMERO 12,345
VOLUMEN 210
En la ciudad de Querétaro, Querétaro, a 15 de marzo de 2019, ante mí, LIC. ROBERTO SALINAS
MORA, titular de la Notaría Pública No. 15 de esta demarcación, comparecen por una parte
el señor ARTURO MÉNDEZ RÍOS, en lo sucesivo "LA PARTE VENDEDORA", y por la otra
INMOBILIARIA DEL NORTE, S.A. DE C.V., con RFC {RFC}, en lo sucesivo "LA PARTE
COMPRADORA", para formalizar el CONTRATO DE COMPRAVENTA al tenor de las siguientes:

CLÁUSULAS
PRIMERA.- La parte vendedora vende a la parte compradora el inmueble ubicado en
Avenida Constituyentes número 450, Colonia El Jacal, C.P. 76180, municipio de Querétaro,
Querétaro, identificado como lote 7 de la manzana 12, con clave catastral 14-01-012-007,
con una superficie de terreno de 1,250.00 m2 (mil doscientos cincuenta metros cuadrados).
SEGUNDA.- El precio de la operación es la cantidad pactada entre las partes.
TERCERA.- La parte vendedora declara que el inmueble se encuentra al corriente en el pago
del impuesto predial.
Inscrita en el Registro Público de la Propiedad bajo el folio real 245789.
DOY FE.
"""

PREDIAL = """MUNICIPIO DE QUERÉTARO · SECRETARÍA DE FINANZAS
RECIBO DE PAGO DEL IMPUESTO PREDIAL
Ejercicio fiscal: 2026   Periodo: 1er a 6to bimestre 2026
Fecha de pago: 12/01/2026
Clave catastral: 14-01-012-007
Contribuyente: {prop}
Ubicación del predio: AV. CONSTITUYENTES #450, COL. EL JACAL, QUERÉTARO, QRO. C.P. 76180
Superficie de terreno: 1,250 m2    Superficie de construcción: 980 m2
Valor catastral: $8,450,000.00
Total pagado: $21,300.00
"""

PREDIAL_OTRO = """MUNICIPIO DE CORREGIDORA · TESORERÍA MUNICIPAL
RECIBO DE PAGO DEL IMPUESTO PREDIAL
Ejercicio fiscal: 2026
Clave catastral: 06-03-114-021
Contribuyente: LAURA GÓMEZ PRIETO
Ubicación del predio: CALLE ROBLE 18, FRACC. LOS OLIVOS, CORREGIDORA, QRO.
Superficie de terreno: 160 m2
"""

ALINEAMIENTO = """H. AYUNTAMIENTO DE QUERÉTARO
SECRETARÍA DE DESARROLLO URBANO
CONSTANCIA DE ALINEAMIENTO Y NÚMERO OFICIAL
Folio: DU/ALN/2025/0881
Fecha de expedición: 10 de febrero de 2026
Se asigna al predio ubicado en Avenida Constituyentes, Colonia El Jacal, municipio de
Querétaro, con clave catastral 14-01-012-007, el NÚMERO OFICIAL {num}.
ALINEAMIENTO: el paramento del predio coincide con el alineamiento oficial de la vía pública;
sin restricciones ni afectaciones por derecho de vía.
Superficie del predio: 1,250.00 m2
Vigencia: un año a partir de su expedición.
"""

USO_SUELO = """H. AYUNTAMIENTO DE QUERÉTARO
SECRETARÍA DE DESARROLLO URBANO
LICENCIA DE USO DE SUELO  Folio: DU/US/2026/0102
Fecha de expedición: 20 de febrero de 2026
Ubicación: Av. Constituyentes No. 450, Col. El Jacal, Querétaro, Qro. Clave catastral 14-01-012-007
Solicitante: INMOBILIARIA DEL NORTE, S.A. DE C.V.
Zonificación: {zona}
Uso de suelo autorizado: {uso}
Superficie aplicable: 1,250.00 m2
Condicionantes: deberá contar con 12 cajones de estacionamiento y respetar horario de
carga y descarga de 07:00 a 10:00 horas.
Vigencia: 2 años a partir de su expedición.
"""


def pdf_texto(ruta: Path, texto: str):
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_textbox(fitz.Rect(50, 50, 560, 800), texto, fontsize=10, fontname="helv")
    doc.save(ruta)


def pdf_escaneado(ruta: Path, texto: str):
    """Rasteriza la página para simular un escaneo (sin capa de texto)."""
    tmp = fitz.open()
    p = tmp.new_page()
    p.insert_textbox(fitz.Rect(50, 50, 560, 800), texto, fontsize=10, fontname="helv")
    pix = p.get_pixmap(dpi=200)
    out = fitz.open()
    np = out.new_page(width=p.rect.width, height=p.rect.height)
    np.insert_image(np.rect, pixmap=pix)
    out.save(ruta)


def main():
    ok, mal = RAIZ / "ok", RAIZ / "problemas"
    ok.mkdir(parents=True, exist_ok=True)
    mal.mkdir(parents=True, exist_ok=True)

    pdf_escaneado(ok / "doc_a.pdf", ESCRITURA)
    pdf_texto(ok / "doc_b.pdf", PREDIAL.format(prop="INMOBILIARIA DEL NORTE SA DE CV"))
    pdf_texto(ok / "doc_c.pdf", ALINEAMIENTO.format(num="450"))
    pdf_texto(ok / "doc_d.pdf", USO_SUELO.format(zona="CU (Corredor Urbano)",
                                                 uso="Comercial y de servicios: tienda de autoservicio"))

    pdf_escaneado(mal / "escritura.pdf", ESCRITURA)
    pdf_texto(mal / "predial.pdf", PREDIAL.format(prop="ARTURO MÉNDEZ RÍOS"))
    pdf_texto(mal / "predial_2.pdf", PREDIAL_OTRO)
    pdf_texto(mal / "alineamiento.pdf", ALINEAMIENTO.format(num="452-B"))
    pdf_texto(mal / "uso.pdf", USO_SUELO.format(zona="H2 (Habitacional densidad baja)",
                                                uso="Habitacional unifamiliar"))
    (mal / "notas.txt").write_text("lista del super", encoding="utf-8")
    print("Ejemplos en", RAIZ)


if __name__ == "__main__":
    main()
