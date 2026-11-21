"use client";

import { Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FileUpload } from "@/components/ui/file-upload";
import { AGENT_PIPELINE_STEPS, DICTAMEN_CIERRE } from "@/lib/workspace/agent-pipeline";
import type { UsoRequerido } from "@/lib/contracts";

export function CargaView({
  files,
  uso,
  isRunning,
  error,
  elapsedSec,
  onUsoChange,
  onFilesAdded,
  onRemoveByIndex,
  onClear,
  onAnalizar,
}: {
  files: File[];
  uso: UsoRequerido;
  isRunning: boolean;
  error: string | null;
  elapsedSec: number | null;
  onUsoChange: (uso: UsoRequerido) => void;
  onFilesAdded: (newFiles: File[]) => void;
  onRemoveByIndex: (index: number) => void;
  onClear: () => void;
  onAnalizar: () => void;
}) {
  return (
    <div className="flex flex-col gap-6">
      <Card className="border-border bg-white">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-base">
              Subir documentos del expediente
            </CardTitle>
            <Badge variant="secondary" className="border-border text-primary">
              {files.length} archivo{files.length === 1 ? "" : "s"}
            </Badge>
          </div>
          <CardDescription>
            Recepción clasifica por contenido. No hace falta etiquetar cada
            archivo. Elige el uso requerido: tienda o CEDIS.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex max-w-sm flex-col gap-1.5 text-sm font-medium text-foreground">
            Uso requerido
            <select
              value={uso}
              disabled={isRunning}
              onChange={(event) =>
                onUsoChange(event.target.value as UsoRequerido)
              }
              className="h-9 rounded-lg border border-border bg-white px-3 text-sm font-normal text-foreground"
            >
              <option value="tienda">Tienda (comercial)</option>
              <option value="cedis">CEDIS (bodega / industrial)</option>
            </select>
          </label>

          <div className="w-full rounded-xl border border-dashed border-border bg-white">
            <FileUpload
              files={files}
              multiple
              onChange={onFilesAdded}
              onRemove={onRemoveByIndex}
              onClear={onClear}
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              disabled={files.length === 0 || isRunning}
              onClick={onAnalizar}
            >
              {isRunning ? "Analizando en el grafo…" : "Analizar expediente"}
            </Button>
            {elapsedSec !== null && (
              <span className="text-xs text-muted-foreground">
                {elapsedSec.toFixed(1)} s
              </span>
            )}
          </div>

          {error && (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="border-border bg-white">
        <CardHeader>
          <CardTitle className="text-base">Qué corre en el backend</CardTitle>
          <CardDescription>
            {isRunning
              ? "El grafo está en curso. Estos pasos no se marcan aquí: la bitácora real aparece al terminar."
              : "El orden lo decide el grafo. Los cuatro especialistas corren en paralelo cuando hay documento de ese tipo."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ol className="space-y-1.5 text-sm text-foreground">
            {AGENT_PIPELINE_STEPS.map((step) => (
              <li key={step.id}>{step.label}</li>
            ))}
          </ol>
          <div className="flex items-start gap-2.5 rounded-lg border border-border bg-secondary/40 p-4 text-xs leading-relaxed text-muted-foreground">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            <p>
              <span className="font-semibold text-foreground">
                {DICTAMEN_CIERRE.label}.
              </span>{" "}
              {DICTAMEN_CIERRE.detail}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
