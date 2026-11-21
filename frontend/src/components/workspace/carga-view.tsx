"use client";

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
import { DocumentoLadoALado } from "@/components/workspace/documento-lado-a-lado";
import type { AnalisisEstado, UsoRequerido } from "@/lib/contracts";

export function CargaView({
  files,
  uso,
  isRunning,
  error,
  elapsedSec,
  analisis,
  manuales,
  onUsoChange,
  onFilesAdded,
  onRemoveByIndex,
  onClear,
  onAnalizar,
  onManualChange,
  onVerDictamen,
}: {
  files: File[];
  uso: UsoRequerido;
  isRunning: boolean;
  error: string | null;
  elapsedSec: number | null;
  analisis: AnalisisEstado | null;
  manuales: Record<string, string>;
  onUsoChange: (uso: UsoRequerido) => void;
  onFilesAdded: (newFiles: File[]) => void;
  onRemoveByIndex: (index: number) => void;
  onClear: () => void;
  onAnalizar: () => void;
  onManualChange: (documentoId: string, nombre: string, valor: string) => void;
  onVerDictamen: () => void;
}) {
  return (
    <div className="flex flex-col gap-6">
      <Card className="border-border bg-white">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-base">Documentos y uso</CardTitle>
            <Badge variant="secondary" className="border-border text-primary">
              {files.length} archivo{files.length === 1 ? "" : "s"}
            </Badge>
          </div>
          <CardDescription>
            Elige tienda o CEDIS y sube los PDF. Al analizar, Recepción dice qué
            documento es y cada especialista lista los campos que encontró.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex max-w-sm flex-col gap-1.5 text-sm font-medium text-foreground">
            Uso requerido
            <select
              value={uso}
              disabled={isRunning}
              onChange={(event) => onUsoChange(event.target.value as UsoRequerido)}
              className="h-9 rounded-lg border border-border bg-white px-3 text-sm font-normal"
            >
              <option value="tienda">Tienda (comercial)</option>
              <option value="cedis">CEDIS (bodega / industrial)</option>
            </select>
          </label>
          <div className="rounded-xl border border-dashed border-border">
            <FileUpload
              files={files}
              multiple
              onChange={onFilesAdded}
              onRemove={onRemoveByIndex}
              onClear={onClear}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" disabled={files.length === 0 || isRunning} onClick={onAnalizar}>
              {isRunning ? "Leyendo documentos…" : analisis ? "Volver a analizar" : "Detectar campos"}
            </Button>
            {analisis && (
              <Button type="button" variant="outline" onClick={onVerDictamen}>
                Ver dictamen
              </Button>
            )}
            {elapsedSec !== null && (
              <span className="text-xs text-muted-foreground">{elapsedSec.toFixed(1)} s</span>
            )}
          </div>
          {error && (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      {analisis && (
        <section className="flex flex-col gap-3">
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Campos según el documento
            </h2>
            <p className="text-sm text-muted-foreground">
              El PDF queda a la izquierda. A la derecha, lo que el especialista
              detectó. Si falta un dato, escríbelo: queda como captura manual y
              no vuelve a correr el grafo.
            </p>
          </div>
          <DocumentoLadoALado
            files={files}
            resultados={analisis.resultados_verificados}
            manuales={manuales}
            editable
            onManualChange={onManualChange}
          />
        </section>
      )}
    </div>
  );
}
