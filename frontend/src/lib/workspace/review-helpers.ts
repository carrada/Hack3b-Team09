import {
  CAMPOS_POR_TIPO_DOCUMENTO,
  type CampoExtraido,
  type DocumentoRevision,
  type RevalidarExpedientePayload,
  type TipoDocumento,
} from "@/lib/contracts";

export function inferirTipoDocumentoPorNombre(nombreArchivo: string): TipoDocumento {
  const lower = nombreArchivo.toLowerCase();
  if (lower.includes("escritura")) return "escritura";
  if (lower.includes("predial")) return "predial";
  if (
    lower.includes("alineamiento") ||
    lower.includes("numero") ||
    lower.includes("número")
  ) {
    return "alineamiento_numero_oficial";
  }
  if (lower.includes("suelo") || lower.includes("uso")) return "uso_de_suelo";
  return "otro";
}

export function crearCamposIniciales(
  tipo: TipoDocumento,
  previos?: CampoExtraido[],
): CampoExtraido[] {
  const previosPorClave = new Map(
    (previos ?? []).map((campo) => [campo.clave, campo]),
  );

  return CAMPOS_POR_TIPO_DOCUMENTO[tipo].map((def) => {
    const existente = previosPorClave.get(def.clave);
    if (existente) {
      return {
        ...existente,
        etiqueta: def.etiqueta,
      };
    }

    return {
      clave: def.clave,
      etiqueta: def.etiqueta,
      valorDetectado: null,
      valorActual: null,
      confianza: null,
      estado: "no_detectado",
      editadoManualmente: false,
      evidencia: null,
    };
  });
}

export function crearDocumentoRevisionDesdeArchivo(
  file: File,
  index: number,
): DocumentoRevision {
  const tipo = inferirTipoDocumentoPorNombre(file.name);
  return {
    documentoId: `local-${file.lastModified}-${index}-${file.size}`,
    nombreArchivo: file.name,
    tipoDetectado: tipo,
    tipoSeleccionado: tipo,
    confianzaClasificacion: null,
    tamanoBytes: file.size,
    campos: crearCamposIniciales(tipo),
  };
}

export function cambiarTipoDocumentoRevision(
  doc: DocumentoRevision,
  nuevoTipo: TipoDocumento,
): DocumentoRevision {
  if (doc.tipoSeleccionado === nuevoTipo) return doc;
  return {
    ...doc,
    tipoSeleccionado: nuevoTipo,
    campos: crearCamposIniciales(nuevoTipo, doc.campos),
  };
}

export function actualizarCampoDocumento(
  doc: DocumentoRevision,
  clave: string,
  nuevoValor: string,
): DocumentoRevision {
  const valorLimpio = nuevoValor.trim();
  return {
    ...doc,
    campos: doc.campos.map((campo) => {
      if (campo.clave !== clave) return campo;

      const valorFinal = valorLimpio.length > 0 ? valorLimpio : null;
      const coincideConOriginal = valorFinal === campo.valorDetectado;

      if (coincideConOriginal) {
        return {
          ...campo,
          valorActual: campo.valorDetectado,
          editadoManualmente: false,
          estado:
            campo.valorDetectado === null
              ? "no_detectado"
              : campo.confianza !== null && campo.confianza < 0.75
                ? "dudoso"
                : "detectado",
        };
      }

      return {
        ...campo,
        valorActual: valorFinal,
        editadoManualmente: true,
        estado: valorFinal === null ? "no_detectado" : "editado_manual",
      };
    }),
  };
}

export function restaurarCampoDocumento(
  doc: DocumentoRevision,
  clave: string,
): DocumentoRevision {
  return {
    ...doc,
    campos: doc.campos.map((campo) => {
      if (campo.clave !== clave) return campo;
      const estadoOriginal =
        campo.valorDetectado === null
          ? "no_detectado"
          : campo.confianza !== null && campo.confianza < 0.75
            ? "dudoso"
            : "detectado";
      return {
        ...campo,
        valorActual: campo.valorDetectado,
        editadoManualmente: false,
        estado: estadoOriginal,
      };
    }),
  };
}

export function construirPayloadRevalidacion(
  documentos: DocumentoRevision[],
  expedienteId?: string,
): RevalidarExpedientePayload {
  return {
    ...(expedienteId ? { expedienteId } : {}),
    documentos: documentos.map((doc) => ({
      documentoId: doc.documentoId,
      nombreArchivo: doc.nombreArchivo,
      tipoDocumento: doc.tipoSeleccionado,
      overrides: doc.campos
        .filter((campo) => campo.editadoManualmente && campo.valorActual !== null)
        .map((campo) => ({
          clave: campo.clave,
          valorOriginal: campo.valorDetectado,
          valorCorregido: campo.valorActual as string,
        })),
    })),
  };
}

export function contarResumenRevision(documentos: DocumentoRevision[]) {
  let totalCampos = 0;
  let camposPorRevisar = 0;
  let camposEditados = 0;
  let camposCompletos = 0;

  for (const doc of documentos) {
    for (const campo of doc.campos) {
      totalCampos += 1;
      if (campo.estado === "no_detectado" || campo.estado === "dudoso") {
        camposPorRevisar += 1;
      }
      if (campo.editadoManualmente) {
        camposEditados += 1;
      }
      if (campo.valorActual !== null && campo.valorActual.trim().length > 0) {
        camposCompletos += 1;
      }
    }
  }

  return {
    totalCampos,
    camposPorRevisar,
    camposEditados,
    camposCompletos,
  };
}
