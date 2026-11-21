import type { TipoDocBackend, TipoDocumento } from "@/lib/contracts";

const ETIQUETAS: Record<string, string> = {
  propietario: "Propietario o titular",
  tipo_persona: "Tipo de persona",
  curp_rfc_propietario: "CURP o RFC",
  direccion: "Dirección",
  numero_oficial: "Número oficial",
  colonia: "Colonia",
  codigo_postal: "Código postal",
  municipio: "Municipio",
  lote_manzana: "Lote y manzana",
  clave_catastral: "Clave catastral",
  superficie: "Superficie",
  superficie_construccion: "Superficie de construcción",
  numero_escritura: "Número de escritura",
  notaria: "Notaría",
  fecha_escritura: "Fecha de escritura",
  folio_real: "Folio real",
  acto_juridico: "Acto jurídico",
  periodo_pagado: "Periodo pagado",
  fecha_pago: "Fecha de pago",
  autoridad_emisora: "Autoridad emisora",
  alineamiento: "Alineamiento",
  fecha_emision: "Fecha de emisión",
  vigencia: "Vigencia",
  folio_documento: "Folio del documento",
  uso_autorizado: "Uso autorizado",
  zonificacion: "Zonificación",
  restricciones: "Restricciones",
};

export function etiquetaCampo(nombre: string): string {
  const conocida = ETIQUETAS[nombre];
  if (conocida) return conocida;
  const texto = nombre.replaceAll("_", " ");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export function claveManual(documentoId: string, nombre: string): string {
  return `${documentoId}::${nombre}`;
}

export function tipoVista(tipo: TipoDocBackend): TipoDocumento {
  if (tipo === "escrituras") return "escritura";
  if (tipo === "alineamiento") return "alineamiento_numero_oficial";
  if (tipo === "uso_suelo") return "uso_de_suelo";
  return "predial";
}

export function archivoDe(files: readonly File[], nombre: string): File | undefined {
  return (
    files.find((file) => file.name === nombre) ??
    files.find((file) => nombre.endsWith(file.name))
  );
}
