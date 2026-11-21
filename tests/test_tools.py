from datetime import date

from expediente.tools import (calcular_vigencia, comparar_direcciones, comparar_nombres, comparar_superficies,
                              corregir_ocr_id, digito_curp, numero_oficial_normalizado, parse_fecha,
                              parse_superficie, sanitizar_entrada_kb, validar_curp, validar_rfc, verificar_cita)


def test_rfc_ejemplo_sat():
    assert validar_rfc.invoke({"rfc": "GODE561231GR8"})["valida"]
    assert not validar_rfc.invoke({"rfc": "GODE561231GR9"})["valida"]


def test_curp_digito():
    c17 = "GODE561231HDFRRN0"
    assert validar_curp.invoke({"curp": c17 + digito_curp(c17)})["valida"]
    assert not validar_curp.invoke({"curp": c17 + "X"})["valida"]


def test_correccion_ocr():
    assert corregir_ocr_id("GODE56I23IGR8") == "GODE561231GR8"
    assert corregir_ocr_id("GODE561231GR9") is None


def test_direcciones():
    assert comparar_direcciones.invoke({"a": "Av. Hidalgo No. 12, Col. Centro", "b": "AVENIDA HIDALGO #12 COLONIA CENTRO"}) >= 85
    assert comparar_direcciones.invoke({"a": "Av. Hidalgo 12", "b": "Calle Morelos 450, Col. Jardines"}) < 60
    assert comparar_direcciones.invoke({"a": "Av. Hidalgo 12", "b": "Av. Hidalgo 98"}) <= 70


def test_nombres():
    assert comparar_nombres.invoke({"a": "C. JUAN PÉREZ LÓPEZ", "b": "Perez Lopez Juan"}) >= 95
    assert comparar_nombres.invoke({"a": "Inmobiliaria del Norte, S.A. de C.V.", "b": "INMOBILIARIA DEL NORTE SA DE CV"}) >= 95
    assert comparar_nombres.invoke({"a": "Juan Pérez", "b": "Laura Gómez Prieto"}) < 60


def test_superficies():
    assert parse_superficie("1,234.56 m2") == 1234.56
    assert parse_superficie("1.234,56 m²") == 1234.56
    assert parse_superficie("2.5 ha") == 25000
    assert parse_superficie("0-45-20 has") == 4520
    r = comparar_superficies.invoke({"a": "1,250 m2", "b": "1,300 m2", "tolerancia": 0.05})
    assert r["comparable"] and r["dentro_tolerancia"]


def test_fechas_y_vigencia():
    assert parse_fecha("15 de marzo de 2023") == date(2023, 3, 15)
    assert parse_fecha("15-mar-2023") == date(2023, 3, 15)
    assert calcular_vigencia.invoke({"fecha_emision": "2025-01-10", "vigencia": "un año", "fecha_ref": "2026-11-21"})["estado"] == "vencido"
    assert calcular_vigencia.invoke({"fecha_emision": "2026-06-10", "vigencia": "2 años", "fecha_ref": "2026-11-21"})["estado"] == "vigente"
    assert calcular_vigencia.invoke({"fecha_emision": "2026-06-10", "vigencia": "indefinida", "fecha_ref": "2026-11-21"})["estado"] == "sin_vencimiento"
    assert calcular_vigencia.invoke({"fecha_emision": None, "vigencia": None, "fecha_ref": "2026-11-21"})["estado"] == "indeterminable"


def test_numero_oficial():
    assert numero_oficial_normalizado("#12-A") == "12a"
    assert numero_oficial_normalizado("S/N") == "sn"


def test_cita():
    assert verificar_cita.invoke({"texto_pagina": "ubicado en la calle  Hidalgo número 12,\nColonia Centro",
                                  "fragmento": "calle Hidalgo número 12, Colonia Centro"}) == 100


def test_kb_sin_datos_personales():
    assert sanitizar_entrada_kb("Notaría Pública No. 15, Lic. Juan Pérez") == "Notaría Pública No. 15"
