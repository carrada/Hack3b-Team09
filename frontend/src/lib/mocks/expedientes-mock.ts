import {
  CrearExpedienteInput,
  CrearExpedienteResponse,
  DOCUMENTOS_MINIMOS_RETO_1,
  ExpedienteAnalisis,
  ExpedienteResumen,
  TipoDocumento,
} from "@/lib/contracts";

const MOCK_DELAY_MS = 220;

const initialMockExpedientes: ExpedienteAnalisis[] = [
  {
    expedienteId: "exp-demo-001",
    nombreExpediente: "Predio Comercial Norte (Ejemplo)",
    estado: "completado",
    creadoEn: "2026-11-21T14:10:00.000Z",
    actualizadoEn: "2026-11-21T14:10:42.000Z",
    nivelConfianza: 0.91,
    recomendacion: "requiere_revision",
    resumenEjecutivo:
      "El expediente contiene los 4 documentos mínimos y el uso de suelo autoriza comercio/minisúper, pero existe una discrepancia de superficie entre la Escritura (480 m²) y el Predial (445 m²) además de una condicionante de cajones de estacionamiento.",
    documentosRecibidos: [
      {
        id: "doc-001-esc",
        nombreArchivo: "escritura_predio_norte.pdf",
        tipoDetectado: "escritura",
        confianzaClasificacion: 0.98,
        paginas: 14,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-001-pre",
        nombreArchivo: "predial_2026_norte.pdf",
        tipoDetectado: "predial",
        confianzaClasificacion: 0.97,
        paginas: 1,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-001-ali",
        nombreArchivo: "alineamiento_numero_oficial_norte.pdf",
        tipoDetectado: "alineamiento_numero_oficial",
        confianzaClasificacion: 0.95,
        paginas: 2,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-001-uso",
        nombreArchivo: "licencia_uso_suelo_norte.pdf",
        tipoDetectado: "uso_de_suelo",
        confianzaClasificacion: 0.96,
        paginas: 3,
        estadoProcesamiento: "procesado",
      },
    ],
    documentosFaltantes: [],
    datosExtraidos: [
      {
        documentoId: "doc-001-esc",
        tipoDocumento: "escritura",
        campos: {
          propietario: "Inmobiliaria Ejemplo del Valle S.A. de C.V.",
          direccion: "Av. Reforma Poniente #214, Col. Centro",
          superficieTerrenoM2: 480,
          folioReal: "FR-0098412",
        },
        evidencias: [
          {
            documentoId: "doc-001-esc",
            nombreArchivo: "escritura_predio_norte.pdf",
            tipoDocumento: "escritura",
            pagina: 3,
            fragmento:
              "Superficie total de terreno de 480.00 metros cuadrados, ubicado en Av. Reforma Poniente número 214.",
          },
        ],
      },
      {
        documentoId: "doc-001-pre",
        tipoDocumento: "predial",
        campos: {
          contribuyente: "Inmobiliaria Ejemplo del Valle S.A. de C.V.",
          direccion: "Av. Reforma Poniente 214, Col. Centro",
          cuentaPredial: "042-118-09-001",
          superficieRegistradaM2: 445,
        },
        evidencias: [
          {
            documentoId: "doc-001-pre",
            nombreArchivo: "predial_2026_norte.pdf",
            tipoDocumento: "predial",
            pagina: 1,
            fragmento:
              "Cuenta predial 042-118-09-001 · Superficie de terreno registrada: 445.00 m².",
          },
        ],
      },
      {
        documentoId: "doc-001-uso",
        tipoDocumento: "uso_de_suelo",
        campos: {
          usoAutorizado: "Comercial — Minisúper / Tienda de autoservicio",
          compatibilidadComercial: true,
          restricciones: "Requiere 6 cajones de estacionamiento mínimo",
          vigencia: "2026-12-31",
          autoridadEmisora: "Dirección de Desarrollo Urbano Municipal",
        },
        evidencias: [
          {
            documentoId: "doc-001-uso",
            nombreArchivo: "licencia_uso_suelo_norte.pdf",
            tipoDocumento: "uso_de_suelo",
            pagina: 2,
            fragmento:
              "Se autoriza el uso comercial para minisúper sujeto a acreditar al menos 6 cajones de estacionamiento.",
          },
        ],
      },
    ],
    validaciones: [
      {
        id: "val-001-uso",
        categoria: "Uso de Suelo",
        criterio: "Compatibilidad con giro comercial requerido",
        estado: "cumple",
        severidad: "alta",
        detalle:
          "El documento autoriza expresamente el giro comercial de minisúper con vigencia al ejercicio actual.",
        evidencias: [
          {
            documentoId: "doc-001-uso",
            nombreArchivo: "licencia_uso_suelo_norte.pdf",
            tipoDocumento: "uso_de_suelo",
            pagina: 2,
            fragmento: "Se autoriza el uso comercial para minisúper.",
          },
        ],
      },
      {
        id: "val-001-sup",
        categoria: "Validación cruzada",
        criterio: "Consistencia de superficie entre Escritura y Predial",
        estado: "requiere_revision",
        severidad: "media",
        detalle:
          "Diferencia de 35 m² (7.3%) entre la superficie escriturada y la superficie catastral en boleta predial.",
        evidencias: [
          {
            documentoId: "doc-001-esc",
            nombreArchivo: "escritura_predio_norte.pdf",
            tipoDocumento: "escritura",
            pagina: 3,
            fragmento: "Superficie total de terreno de 480.00 metros cuadrados.",
          },
          {
            documentoId: "doc-001-pre",
            nombreArchivo: "predial_2026_norte.pdf",
            tipoDocumento: "predial",
            pagina: 1,
            fragmento: "Superficie de terreno registrada: 445.00 m².",
          },
        ],
      },
    ],
    inconsistencias: [
      {
        id: "inc-001-superficie",
        campo: "Superficie del terreno",
        descripcion:
          "La superficie declarada en la Escritura no coincide con la superficie registrada en la boleta de Predial.",
        severidad: "media",
        hallazgos: [
          {
            documentoId: "doc-001-esc",
            nombreArchivo: "escritura_predio_norte.pdf",
            tipoDocumento: "escritura",
            valorEncontrado: "480.00 m²",
            evidencia: {
              documentoId: "doc-001-esc",
              nombreArchivo: "escritura_predio_norte.pdf",
              tipoDocumento: "escritura",
              pagina: 3,
              fragmento:
                "Superficie total de terreno de 480.00 metros cuadrados.",
            },
          },
          {
            documentoId: "doc-001-pre",
            nombreArchivo: "predial_2026_norte.pdf",
            tipoDocumento: "predial",
            valorEncontrado: "445.00 m²",
            evidencia: {
              documentoId: "doc-001-pre",
              nombreArchivo: "predial_2026_norte.pdf",
              tipoDocumento: "predial",
              pagina: 1,
              fragmento: "Superficie de terreno registrada: 445.00 m².",
            },
          },
        ],
      },
    ],
    requisitosCumplidos: [
      "Expediente completo con los 4 tipos documentales mínimos.",
      "Coincidencia de propietario y dirección en los 4 documentos.",
      "Uso de suelo comercial vigente compatible con tienda de autoservicio.",
    ],
    requisitosNoCumplidos: [
      "Diferencia de superficie de 35 m² pendiente de aclaración catastral.",
      "Validar cumplimiento de 6 cajones de estacionamiento condicionados en Uso de Suelo.",
    ],
    trazaAgentes: [
      {
        agente: "Clasificador Documental",
        estado: "completado",
        resumen: "4 documentos clasificados con confianza promedio de 96.5%.",
        duracionMs: 1420,
      },
      {
        agente: "Extractor Especializado",
        estado: "completado",
        resumen: "Entidades clave extraídas con citas de página y fragmento.",
        duracionMs: 4180,
      },
      {
        agente: "Validador Cruzado",
        estado: "completado",
        resumen: "Detectó 1 discrepancia de superficie entre Escritura y Predial.",
        duracionMs: 2050,
      },
      {
        agente: "Dictaminador Legal",
        estado: "completado",
        resumen: "Recomendación emitida: Requiere revisión.",
        duracionMs: 1310,
      },
    ],
  },
  {
    expedienteId: "exp-demo-002",
    nombreExpediente: "Local Sur Industrial (Ejemplo)",
    estado: "completado",
    creadoEn: "2026-11-21T13:30:00.000Z",
    actualizadoEn: "2026-11-21T13:30:38.000Z",
    nivelConfianza: 0.95,
    recomendacion: "cumple",
    resumenEjecutivo:
      "Los 4 documentos están completos, vigentes y son consistentes en titularidad, domicilio, número oficial y superficie. Uso de suelo comercial sin restricciones bloqueantes.",
    documentosRecibidos: [
      {
        id: "doc-002-esc",
        nombreArchivo: "escritura_sur.pdf",
        tipoDetectado: "escritura",
        confianzaClasificacion: 0.99,
        paginas: 10,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-002-pre",
        nombreArchivo: "predial_sur.pdf",
        tipoDetectado: "predial",
        confianzaClasificacion: 0.98,
        paginas: 1,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-002-ali",
        nombreArchivo: "alineamiento_sur.pdf",
        tipoDetectado: "alineamiento_numero_oficial",
        confianzaClasificacion: 0.97,
        paginas: 1,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-002-uso",
        nombreArchivo: "uso_suelo_sur.pdf",
        tipoDetectado: "uso_de_suelo",
        confianzaClasificacion: 0.98,
        paginas: 2,
        estadoProcesamiento: "procesado",
      },
    ],
    documentosFaltantes: [],
    datosExtraidos: [],
    validaciones: [],
    inconsistencias: [],
    requisitosCumplidos: [
      "Expediente completo (4/4 tipos documentales).",
      "Consistencia total de propietario, domicilio, número oficial y superficie.",
      "Uso de suelo comercial vigente y compatible.",
    ],
    requisitosNoCumplidos: [],
    trazaAgentes: [
      {
        agente: "Clasificador Documental",
        estado: "completado",
        resumen: "4/4 documentos identificados.",
        duracionMs: 1120,
      },
      {
        agente: "Validador Cruzado",
        estado: "completado",
        resumen: "Sin inconsistencias detectadas.",
        duracionMs: 1780,
      },
      {
        agente: "Dictaminador Legal",
        estado: "completado",
        resumen: "Recomendación emitida: Cumple.",
        duracionMs: 980,
      },
    ],
  },
  {
    expedienteId: "exp-demo-003",
    nombreExpediente: "Predio Poniente Habitacional (Ejemplo)",
    estado: "completado",
    creadoEn: "2026-11-21T12:15:00.000Z",
    actualizadoEn: "2026-11-21T12:15:29.000Z",
    nivelConfianza: 0.93,
    recomendacion: "no_cumple",
    resumenEjecutivo:
      "Falta la constancia de Alineamiento y Número Oficial y el Uso de Suelo corresponde exclusivamente a zona habitacional H2 sin autorización comercial.",
    documentosRecibidos: [
      {
        id: "doc-003-esc",
        nombreArchivo: "escritura_poniente.pdf",
        tipoDetectado: "escritura",
        confianzaClasificacion: 0.96,
        paginas: 8,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-003-pre",
        nombreArchivo: "predial_poniente.pdf",
        tipoDetectado: "predial",
        confianzaClasificacion: 0.95,
        paginas: 1,
        estadoProcesamiento: "procesado",
      },
      {
        id: "doc-003-uso",
        nombreArchivo: "uso_suelo_poniente.pdf",
        tipoDetectado: "uso_de_suelo",
        confianzaClasificacion: 0.97,
        paginas: 2,
        estadoProcesamiento: "procesado",
      },
    ],
    documentosFaltantes: ["alineamiento_numero_oficial"],
    datosExtraidos: [],
    validaciones: [
      {
        id: "val-003-uso",
        categoria: "Uso de Suelo",
        criterio: "Compatibilidad con giro comercial requerido",
        estado: "no_cumple",
        severidad: "alta",
        detalle:
          "El certificado establece zonificación H2 Habitacional Unifamiliar; giro comercial prohibido.",
        evidencias: [
          {
            documentoId: "doc-003-uso",
            nombreArchivo: "uso_suelo_poniente.pdf",
            tipoDocumento: "uso_de_suelo",
            pagina: 1,
            fragmento:
              "Zonificación H2 Habitacional Unifamiliar. No se autorizan usos comerciales ni de abasto.",
          },
        ],
      },
    ],
    inconsistencias: [],
    requisitosCumplidos: ["Propietario y domicilio coinciden entre Escritura y Predial."],
    requisitosNoCumplidos: [
      "Falta documento obligatorio: Alineamiento y Número Oficial.",
      "Uso de suelo incompatible con tienda comercial.",
    ],
    trazaAgentes: [
      {
        agente: "Clasificador Documental",
        estado: "completado",
        resumen: "3 documentos recibidos; falta Alineamiento y Número Oficial.",
        duracionMs: 980,
      },
      {
        agente: "Dictaminador Legal",
        estado: "completado",
        resumen: "Recomendación emitida: No cumple.",
        duracionMs: 1090,
      },
    ],
  },
];

const mockStore = new Map<string, ExpedienteAnalisis>(
  initialMockExpedientes.map((item) => [item.expedienteId, item]),
);

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function toResumen(item: ExpedienteAnalisis): ExpedienteResumen {
  return {
    expedienteId: item.expedienteId,
    nombreExpediente: item.nombreExpediente,
    estado: item.estado,
    recomendacion: item.recomendacion,
    nivelConfianza: item.nivelConfianza,
    documentosRecibidosCount: item.documentosRecibidos.length,
    documentosFaltantesCount: item.documentosFaltantes.length,
    inconsistenciasCount: item.inconsistencias.length,
    creadoEn: item.creadoEn,
  };
}

function inferTipoFromFilename(filename: string): TipoDocumento {
  const lower = filename.toLowerCase();
  if (lower.includes("escritura")) return "escritura";
  if (lower.includes("predial")) return "predial";
  if (lower.includes("alineamiento") || lower.includes("numero")) {
    return "alineamiento_numero_oficial";
  }
  if (lower.includes("suelo") || lower.includes("uso")) return "uso_de_suelo";
  return "otro";
}

export async function mockListExpedientes(): Promise<ExpedienteResumen[]> {
  await wait(MOCK_DELAY_MS);
  return Array.from(mockStore.values())
    .sort((a, b) => b.creadoEn.localeCompare(a.creadoEn))
    .map(toResumen);
}

export async function mockGetExpediente(
  expedienteId: string,
): Promise<ExpedienteAnalisis | null> {
  await wait(MOCK_DELAY_MS);
  return mockStore.get(expedienteId) ?? null;
}

export async function mockCreateExpediente(
  input: CrearExpedienteInput,
): Promise<CrearExpedienteResponse> {
  await wait(MOCK_DELAY_MS);
  const now = new Date().toISOString();
  const id = `exp-mock-${Date.now()}`;

  const docs = input.archivos.map((file, index) => ({
    id: `${id}-doc-${index + 1}`,
    nombreArchivo: file.name,
    tipoDetectado: inferTipoFromFilename(file.name),
    confianzaClasificacion: 0.9,
    estadoProcesamiento: "procesado" as const,
  }));

  const presentTypes = new Set(docs.map((doc) => doc.tipoDetectado));
  const missing = DOCUMENTOS_MINIMOS_RETO_1.filter((t) => !presentTypes.has(t));

  const record: ExpedienteAnalisis = {
    expedienteId: id,
    nombreExpediente: input.nombreExpediente,
    estado: "completado",
    creadoEn: now,
    actualizadoEn: now,
    nivelConfianza: missing.length === 0 ? 0.88 : 0.72,
    recomendacion: missing.length === 0 ? "requiere_revision" : "no_cumple",
    resumenEjecutivo:
      missing.length === 0
        ? "Expediente recibido en modo mock. Listo para conectar el pipeline multiagente de LangChain."
        : "Expediente incompleto en modo mock: faltan documentos mínimos obligatorios.",
    documentosRecibidos: docs,
    documentosFaltantes: missing,
    datosExtraidos: [],
    validaciones: [],
    inconsistencias: [],
    requisitosCumplidos:
      docs.length > 0 ? [`Se recibieron ${docs.length} archivo(s).`] : [],
    requisitosNoCumplidos: missing.map(
      (tipo) => `Documento mínimo faltante: ${tipo}.`,
    ),
    trazaAgentes: [
      {
        agente: "Proveedor Mock Local",
        estado: "completado",
        resumen: "Respuesta simulada generada sin invocar el backend.",
        duracionMs: MOCK_DELAY_MS,
      },
    ],
  };

  mockStore.set(id, record);

  return {
    expedienteId: id,
    estado: record.estado,
    creadoEn: now,
  };
}
