"use client";

import ThoughtLine from "@/components/ui/ThoughtLine";
import type { StatusMarkState } from "@/components/ui/StatusMark";
import {
  runningThought,
  thoughtStepsForStatuses,
} from "@/lib/workspace/agent-pipeline";

export function AgentThoughtLine({
  statuses,
  working,
  elapsedSec,
}: {
  statuses: readonly StatusMarkState[];
  working: boolean;
  elapsedSec: number | null;
}) {
  const steps = thoughtStepsForStatuses(statuses);
  const settled = !working && elapsedSec !== null;

  return (
    <ThoughtLine
      working={working}
      steps={steps}
      label={runningThought(statuses)}
      doneLabel={settled ? "Análisis en" : "En espera del análisis"}
      showTimer={working || settled}
      elapsed={elapsedSec ?? undefined}
      glyph="sparkle"
      glyphColor="#E10600"
      color="currentColor"
      fontSize={15}
      collapsible
      collapseOnSettle
      className="thought-line--block text-foreground"
    />
  );
}
