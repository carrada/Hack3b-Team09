"use client";

import { Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FileUpload } from "@/components/ui/file-upload";
import StatusMark from "@/components/ui/StatusMark";
import { FieldReviewPanel } from "@/components/workspace/field-review-panel";
import type { StatusMarkState } from "@/components/ui/StatusMark";
import {
  DOCUMENTOS_MINIMOS_RETO_1,
  TIPO_DOCUMENTO_LABELS,
  type DocumentoRevision,
  type TipoDocumento,
} from "@/lib/contracts";

export function CargaView({
  files,
  documentos,
  confirmedAt,
  isConfirming,
  onFilesAdded,
  onRemoveByIndex,
  onClear,
  onChangeDocType,
  onSaveField,
  onRestoreField,
  onRemoveDoc,
  onConfirmForValidation,
  agentStatuses,
  analysisElapsedSec,
}: {
  files: File[];
  documentos: DocumentoRevision[];
  confirmedAt: string | null;
  isConfirming: boolean;
  onFilesAdded: (newFiles: File[]) => void;
  onRemoveByIndex: (index: number) => void;
  onClear: () => void;
  onChangeDocType: (documentoId: string, tipo: TipoDocumento) => void;
  onSaveField: (documentoId: string, clave: string, valor: string) => void;
  onRestoreField: (documentoId: string, clave: string) => void;
  onRemoveDoc: (documentoId: string) => void;
  onConfirmForValidation: () => void;
  agentStatuses: readonly StatusMarkState[];
  analysisElapsedSec: number | null;
}) {
  const tiposPresentes = new Set(documentos.map((doc) => doc.tipoSeleccionado));
  const completados = DOCUMENTOS_MINIMOS_RETO_1.filter((t) =>
    tiposPresentes.has(t),
  ).length;

  return (
    <div className="flex flex-col gap-6">
      <Card className="border-border bg-white">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-base">
              Subir documentos del expediente
            </CardTitle>
            <Badge variant="secondary" className="border-border text-primary">
              Checklist: {completados}/4 tipos mínimos
            </Badge>
          </div>
          <CardDescription>
            Agrega uno o varios PDFs del inmueble. Puedes quitar archivos
            individuales o limpiar toda la carga directamente dentro del
            cargador.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2.5 rounded-xl border border-border bg-secondary/35 p-3.5 sm:grid-cols-2">
            {DOCUMENTOS_MINIMOS_RETO_1.map((tipo) => {
              const presente = tiposPresentes.has(tipo);
              return (
                <div
                  key={tipo}
                  className="flex items-center justify-between rounded-lg border border-border bg-white px-3 py-2"
                >
                  <StatusMark
                    status={presente ? "done" : "pending"}
                    label={TIPO_DOCUMENTO_LABELS[tipo]}
                    color="#7A0704"
                    doneColor="#22c55e"
                    errorColor="#E10600"
                    size={18}
                    fontSize={13}
                    strike
                  />
                </div>
              );
            })}
          </div>

          <div className="w-full rounded-xl border border-dashed border-border bg-white">
            <FileUpload
              files={files}
              multiple
              onChange={onFilesAdded}
              onRemove={onRemoveByIndex}
              onClear={onClear}
            />
          </div>
        </CardContent>
      </Card>

      {documentos.length === 0 ? (
        <Card className="border-border bg-white">
          <CardContent className="pt-5">
            <div className="flex items-start gap-2.5 rounded-lg border border-border bg-secondary/40 p-4 text-xs leading-relaxed text-muted-foreground">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <p>
                En cuanto subas uno o más documentos arriba, se desplegará aquí
                el{" "}
                <span className="font-semibold text-foreground">
                  panel interactivo de revisión y edición de campos
                </span>{" "}
                para verificar el tipo documental y modificar opcionalmente
                cualquier dato que falte o salga dudoso antes de dictaminar.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <FieldReviewPanel
          documentos={documentos}
          files={files}
          confirmedAt={confirmedAt}
          isConfirming={isConfirming}
          onChangeDocType={onChangeDocType}
          onSaveField={onSaveField}
          onRestoreField={onRestoreField}
          onRemoveDoc={onRemoveDoc}
          onConfirmForValidation={onConfirmForValidation}
          agentStatuses={agentStatuses}
          analysisElapsedSec={analysisElapsedSec}
        />
      )}
    </div>
  );
}
