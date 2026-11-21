import type { StatusMarkState } from "@/components/ui/StatusMark";

export const AGENT_PIPELINE_STEPS = [
  {
    id: "clasificador",
    label: "01 · Clasificador Documental",
    runningMessage: "Clasificando documentos del expediente...",
    thought: "Leyendo y clasificando cada documento",
  },
  {
    id: "extractor",
    label: "02 · Extractor Especializado",
    runningMessage: "Extrayendo campos clave por documento...",
    thought: "Extrayendo los campos de cada tipo documental",
  },
  {
    id: "reglas",
    label: "03 · Validador de Reglas",
    runningMessage: "Evaluando criterios y reglas normativas...",
    thought: "Evaluando reglas y criterios del expediente",
  },
  {
    id: "cruzado",
    label: "04 · Validador Cruzado",
    runningMessage: "Contrastando datos entre documentos...",
    thought: "Cruzando dirección, titular y superficie",
  },
  {
    id: "evidencia",
    label: "05 · Verificador de Evidencia",
    runningMessage: "Anclando hallazgos a página y fragmento...",
    thought: "Anclando cada hallazgo a su página",
  },
  {
    id: "dictaminador",
    label: "06 · Dictaminador y Explicador Legal",
    runningMessage: "Redactando recomendación y justificación...",
    thought: "Redactando la recomendación para el equipo legal",
  },
] as const;

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
