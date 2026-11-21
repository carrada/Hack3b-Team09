import { z } from "zod";

/** Contrato del JSON que devuelve `ejecutar()` vía POST /api/v1/analisis. Snake_case del backend. */

export const UsoRequeridoSchema = z.enum(["tienda", "cedis"]);
export type UsoRequerido = z.infer<typeof UsoRequeridoSchema>;

export const RecomendacionBackendSchema = z.enum([
  "cumple",
  "requiere_revision",
  "no_cumple",
]);
export type RecomendacionBackend = z.infer<typeof RecomendacionBackendSchema>;

export const ETIQUETA_RECOMENDACION: Record<RecomendacionBackend, string> = {
  cumple: "Cumple",
  requiere_revision: "Requiere revisión",
  no_cumple: "No cumple",
};

export const TipoDocBackendSchema = z.enum([
  "escrituras",
  "predial",
  "alineamiento",
  "uso_suelo",
]);
export type TipoDocBackend = z.infer<typeof TipoDocBackendSchema>;

export const NOMBRES_TIPO_BACKEND: Record<TipoDocBackend, string> = {
  escrituras: "Escrituras",
  predial: "Predial",
  alineamiento: "Alineamiento y Número Oficial",
  uso_suelo: "Uso de Suelo",
};

export const EvidenciaBackendSchema = z.object({
  documento_id: z.string(),
  pagina: z.number().int(),
  fragmento: z.string(),
  verificada: z.boolean().optional(),
  score_verificacion: z.number().optional(),
});
export type EvidenciaBackend = z.infer<typeof EvidenciaBackendSchema>;

export const CampoBackendSchema = z.object({
  nombre: z.string(),
  valor: z.string().nullable().optional(),
  evidencia: EvidenciaBackendSchema.nullable().optional(),
  confianza: z.number().optional(),
});
export type CampoBackend = z.infer<typeof CampoBackendSchema>;

export const HallazgoBackendSchema = z.object({
  regla_id: z.string(),
  documento_id: z.string().optional(),
  severidad: z.enum(["critica", "menor", "info"]),
  resultado: RecomendacionBackendSchema,
  descripcion: z.string(),
  evidencias: z.array(EvidenciaBackendSchema).default([]),
});
export type HallazgoBackend = z.infer<typeof HallazgoBackendSchema>;

export const ResultadoDocumentoBackendSchema = z.object({
  documento_id: z.string(),
  nombre_archivo: z.string(),
  tipo: TipoDocBackendSchema,
  agente: z.string(),
  campos: z.array(CampoBackendSchema).default([]),
  hallazgos: z.array(HallazgoBackendSchema).default([]),
  estado: RecomendacionBackendSchema,
  motivos: z.array(z.string()).default([]),
  calidad_ocr: z.number().optional(),
  error: z.string().nullable().optional(),
  obligatorios_encontrados: z.number().optional(),
  obligatorios_total: z.number().optional(),
});
export type ResultadoDocumentoBackend = z.infer<
  typeof ResultadoDocumentoBackendSchema
>;

export const CruceBackendSchema = z.object({
  atributo: z.string(),
  valores: z.record(z.string(), z.string()),
  score: z.number(),
  resultado: z.enum(["coincide", "difiere", "ambiguo"]),
  metodo: z.enum(["exacto", "fuzzy", "numerico", "llm"]),
  explicacion: z.string().optional().default(""),
});
export type CruceBackend = z.infer<typeof CruceBackendSchema>;

export const DiscrepanciaBackendSchema = z.object({
  atributo: z.string(),
  valores: z.record(z.string(), z.string()),
  evidencias: z.array(EvidenciaBackendSchema).default([]),
  severidad: z.enum(["critica", "menor"]),
  explicacion: z.string(),
});
export type DiscrepanciaBackend = z.infer<typeof DiscrepanciaBackendSchema>;

export const DictamenBackendSchema = z.object({
  recomendacion: RecomendacionBackendSchema,
  confianza: z.number(),
  senales_confianza: z.record(z.string(), z.number()).default({}),
  uso_requerido: z.string(),
  documentos_recibidos: z.array(z.string()).default([]),
  documentos_faltantes: z.array(z.string()).default([]),
  documentos_descartados: z.array(z.string()).default([]),
  requisitos_cumplidos: z.array(z.string()).default([]),
  requisitos_no_cumplidos: z.array(z.string()).default([]),
  discrepancias: z.array(DiscrepanciaBackendSchema).default([]),
  razones: z.array(z.string()).default([]),
  resumen: z.string().optional().default(""),
  requiere_humano: z.boolean(),
  puntos_a_verificar: z.array(z.string()).default([]),
  citas_total: z.number().optional(),
  citas_verificadas: z.number().optional(),
});
export type DictamenBackend = z.infer<typeof DictamenBackendSchema>;

export const AnalisisEstadoSchema = z.object({
  dictamen: DictamenBackendSchema,
  bitacora: z.array(z.string()).default([]),
  resultados_verificados: z.array(ResultadoDocumentoBackendSchema).default([]),
  cruces: z.array(CruceBackendSchema).default([]),
  discrepancias: z.array(DiscrepanciaBackendSchema).default([]),
});
export type AnalisisEstado = z.infer<typeof AnalisisEstadoSchema>;
