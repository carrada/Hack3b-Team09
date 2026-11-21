import type { StatusMarkState } from "@/components/ui/StatusMark";

/** Los 6 agentes del grafo, con los textos de la rama backend. El Dictamen es el cierre, no el séptimo. */
export const AGENT_PIPELINE_STEPS = [
  {
    id: "recepcion",
    label: "01 · Recepción",
    runningMessage: "OCR, clasificación por contenido y agrupación...",
    thought: "Recepción: OCR, clasificación por contenido y agrupación",
  },
  {
    id: "escrituras",
    label: "02 · Especialista Escrituras",
    runningMessage: "Extrayendo la escritura y evaluando sus reglas...",
    thought: "Especialista Escrituras: valor, página y fragmento",
  },
  {
    id: "predial",
    label: "03 · Especialista Predial",
    runningMessage: "Extrayendo el predial y evaluando sus reglas...",
    thought: "Especialista Predial: valor, página y fragmento",
  },
  {
    id: "alineamiento",
    label: "04 · Especialista Alineamiento y Número Oficial",
    runningMessage: "Extrayendo alineamiento y número oficial...",
    thought: "Especialista Alineamiento y Número Oficial",
  },
  {
    id: "uso_suelo",
    label: "05 · Especialista Uso de Suelo",
    runningMessage: "Extrayendo uso de suelo y evaluando sus reglas...",
    thought: "Especialista Uso de Suelo",
  },
  {
    id: "validador_cruzado",
    label: "06 · Validador cruzado",
    runningMessage: "Cruzando dirección, número oficial, propietario y superficie...",
    thought: "Validador cruzado: corre siempre",
  },
] as const;

export const DICTAMEN_CIERRE = {
  id: "dictamen",
  label: "Cierre · Dictamen",
  detail:
    "Verifica cada cita contra el OCR, calcula la confianza y emite Cumple, Requiere revisión o No cumple. Si no es Cumple, deja los puntos para la revisión humana.",
} as const;

export function thoughtStepsForStatuses(
  statuses: readonly StatusMarkState[],
): string[] {
  return AGENT_PIPELINE_STEPS.flatMap((step, index) => {
    const status = statuses[index] ?? "pending";
    if (status === "done" || status === "running") return [step.thought];
    return [];
  });
}

export function runningThought(statuses: readonly StatusMarkState[]): string {
  const index = statuses.findIndex((status) => status === "running");
  if (index < 0) return "Analizando el expediente";
  return AGENT_PIPELINE_STEPS[index]?.thought ?? "Analizando el expediente";
}
