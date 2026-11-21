"use client";

import { useRef, useState } from "react";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Code2,
  EyeOff,
  FileText,
  PanelRight,
  Pencil,
  RotateCcw,
  SlidersHorizontal,
  Trash2,
  X,
} from "lucide-react";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { StatusMarkState } from "@/components/ui/StatusMark";
import { AgentThoughtLine } from "@/components/workspace/agent-thought-line";
import { DocumentViewerPane } from "@/components/workspace/document-viewer-pane";
import {
  CAMPOS_POR_TIPO_DOCUMENTO,
  TIPO_DOCUMENTO_LABELS,
  type CampoExtraido,
  type DocumentoRevision,
  type EstadoCampoExtraido,
  type TipoDocumento,
} from "@/lib/contracts";
import {
  construirPayloadRevalidacion,
  contarResumenRevision,
} from "@/lib/workspace/review-helpers";
import { cn } from "@/lib/utils";

type FieldFilter = "todos" | "por_revisar" | "editados";

const TIPO_OPTIONS: readonly TipoDocumento[] = [
  "escritura",
  "predial",
  "alineamiento_numero_oficial",
  "uso_de_suelo",
  "otro",
] as const;

function getFieldStatusMeta(estado: EstadoCampoExtraido): {
  label: string;
  variant: BadgeProps["variant"];
} {
  switch (estado) {
    case "detectado":
      return { label: "Detectado IA", variant: "success" };
    case "dudoso":
      return { label: "Confianza baja", variant: "warning" };
    case "no_detectado":
      return { label: "No detectado", variant: "destructive" };
    case "editado_manual":
      return { label: "Corregido manualmente", variant: "secondary" };
  }
}

function getPlaceholder(tipo: TipoDocumento, clave: string): string {
  const def = CAMPOS_POR_TIPO_DOCUMENTO[tipo].find((c) => c.clave === clave);
  return def?.placeholder ?? "Escribe el valor verificado en el documento";
}

function countNeedsReview(doc: DocumentoRevision): number {
  return doc.campos.filter(
    (campo) => campo.estado === "no_detectado" || campo.estado === "dudoso",
  ).length;
}

export function FieldReviewPanel({
  documentos,
  files,
  confirmedAt,
  isConfirming,
  onChangeDocType,
  onSaveField,
  onRestoreField,
  onRemoveDoc,
  onConfirmForValidation,
  agentStatuses,
  analysisElapsedSec,
}: {
  documentos: DocumentoRevision[];
  files: File[];
  confirmedAt: string | null;
  isConfirming: boolean;
  onChangeDocType: (documentoId: string, tipo: TipoDocumento) => void;
  onSaveField: (documentoId: string, clave: string, valor: string) => void;
  onRestoreField: (documentoId: string, clave: string) => void;
  onRemoveDoc: (documentoId: string) => void;
  onConfirmForValidation: () => void;
  agentStatuses: readonly StatusMarkState[];
  analysisElapsedSec: number | null;
}) {
  const [filter, setFilter] = useState<FieldFilter>("todos");
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [draftValue, setDraftValue] = useState("");
  const [showJsonPreview, setShowJsonPreview] = useState(false);
  const [showViewer, setShowViewer] = useState(true);
  const [activeId, setActiveId] = useState(documentos[0]?.documentoId ?? "");
  const [viewerPage, setViewerPage] = useState<number | undefined>(undefined);
  const viewerRef = useRef<HTMLDivElement>(null);

  const resolvedId = documentos.some((doc) => doc.documentoId === activeId)
    ? activeId
    : (documentos[0]?.documentoId ?? "");

  const activeIndex = Math.max(
    0,
    documentos.findIndex((doc) => doc.documentoId === resolvedId),
  );
  const activeDoc = documentos[activeIndex];
  const activeFile = files[activeIndex];

  const summary = contarResumenRevision(documentos);
  const payloadPreview = construirPayloadRevalidacion(documentos);

  const focusDocument = (documentoId: string, page?: number) => {
    setActiveId(documentoId);
    setViewerPage(page && page > 0 ? page : undefined);
    setShowViewer(true);
    if (typeof window !== "undefined" && window.innerWidth < 1280) {
      viewerRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  const startEditing = (documentoId: string, campo: CampoExtraido) => {
    setEditingKey(`${documentoId}::${campo.clave}`);
    setDraftValue(campo.valorActual ?? "");
    focusDocument(documentoId, campo.evidencia?.pagina);
  };

  const cancelEditing = () => {
    setEditingKey(null);
    setDraftValue("");
  };

  const commitEditing = (documentoId: string, clave: string) => {
    onSaveField(documentoId, clave, draftValue);
    setEditingKey(null);
    setDraftValue("");
  };

  const matchesFilter = (campo: CampoExtraido): boolean => {
    if (filter === "por_revisar") {
      return campo.estado === "no_detectado" || campo.estado === "dudoso";
    }
    if (filter === "editados") {
      return campo.editadoManualmente;
    }
    return true;
  };

  const visibleFields = activeDoc ? activeDoc.campos.filter(matchesFilter) : [];
  const typeChanged = activeDoc
    ? activeDoc.tipoSeleccionado !== activeDoc.tipoDetectado
    : false;

  return (
    <Card className="border-border bg-white">
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-base">
              <SlidersHorizontal className="h-4 w-4 text-primary" />
              Revisión y edición junto al documento
            </CardTitle>
            <CardDescription>
              El archivo se queda visible mientras completas o corriges un
              campo. Nada se envía fuera de esta sesión.
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="border-border">
              {summary.camposCompletos}/{summary.totalCampos} con dato
            </Badge>
            {summary.camposEditados > 0 && (
              <Badge variant="secondary" className="border-border text-primary">
                {summary.camposEditados} corrección(es)
              </Badge>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowViewer((prev) => !prev)}
            >
              {showViewer ? (
                <>
                  <EyeOff className="h-3.5 w-3.5" />
                  Ocultar visor
                </>
              ) : (
                <>
                  <PanelRight className="h-3.5 w-3.5" />
                  Mostrar visor
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1">
          {documentos.map((doc) => {
            const pending = countNeedsReview(doc);
            const selected = doc.documentoId === activeDoc?.documentoId;
            return (
              <button
                key={doc.documentoId}
                type="button"
                onClick={() => focusDocument(doc.documentoId)}
                className={cn(
                  "flex min-w-[180px] max-w-[240px] flex-col items-start gap-1 rounded-lg border px-3 py-2 text-left transition-colors",
                  selected
                    ? "border-primary bg-secondary/70"
                    : "border-border bg-white hover:bg-secondary/40",
                )}
              >
                <span className="w-full truncate text-xs font-semibold text-foreground">
                  {doc.nombreArchivo}
                </span>
                <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  {TIPO_DOCUMENTO_LABELS[doc.tipoSeleccionado]}
                  {pending > 0 ? ` · ${pending} por revisar` : " · listo"}
                </span>
              </button>
            );
          })}
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-5">
        {activeDoc && (
          <div
            className={cn(
              "grid items-start gap-5",
              showViewer && "xl:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]",
            )}
          >
            <div className="flex min-w-0 flex-col gap-4">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-secondary/40 px-4 py-3">
                <div className="flex min-w-0 items-center gap-2.5">
                  <FileText className="h-4 w-4 shrink-0 text-primary" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">
                      {activeDoc.nombreArchivo}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activeDoc.confianzaClasificacion !== null
                        ? `Clasificación IA ${Math.round(activeDoc.confianzaClasificacion * 100)}%`
                        : "Listo para extracción del Agente 02"}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <label className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Tipo:</span>
                    <select
                      value={activeDoc.tipoSeleccionado}
                      onChange={(e) =>
                        onChangeDocType(
                          activeDoc.documentoId,
                          e.target.value as TipoDocumento,
                        )
                      }
                      className="rounded-md border border-border bg-white px-2.5 py-1 text-xs font-medium text-foreground focus:border-primary focus:outline-none"
                    >
                      {TIPO_OPTIONS.map((opt) => (
                        <option key={opt} value={opt}>
                          {TIPO_DOCUMENTO_LABELS[opt]}
                        </option>
                      ))}
                    </select>
                  </label>
                  {typeChanged && (
                    <Badge
                      variant="secondary"
                      className="border-border text-primary"
                    >
                      Tipo corregido
                    </Badge>
                  )}
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => onRemoveDoc(activeDoc.documentoId)}
                    aria-label={`Quitar ${activeDoc.nombreArchivo}`}
                    className="h-7 px-2 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-1.5">
                  {(
                    [
                      { id: "todos", label: "Todos" },
                      { id: "por_revisar", label: "Por revisar" },
                      { id: "editados", label: "Corregidos" },
                    ] as const
                  ).map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setFilter(tab.id)}
                      className={cn(
                        "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                        filter === tab.id
                          ? "bg-primary text-primary-foreground"
                          : "border border-border bg-white text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
                      )}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowJsonPreview((prev) => !prev)}
                  className="text-xs text-muted-foreground"
                >
                  <Code2 className="h-3.5 w-3.5" />
                  {showJsonPreview ? "Ocultar payload" : "Ver payload JSON"}
                </Button>
              </div>

              {visibleFields.length === 0 ? (
                <p className="rounded-xl border border-border px-4 py-4 text-xs text-muted-foreground">
                  No hay campos en este documento para el filtro seleccionado.
                </p>
              ) : (
                <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border">
                  {visibleFields.map((campo) => {
                    const rowKey = `${activeDoc.documentoId}::${campo.clave}`;
                    const isEditing = editingKey === rowKey;
                    const statusMeta = getFieldStatusMeta(campo.estado);

                    return (
                      <li
                        key={campo.clave}
                        className={cn(
                          "flex flex-col gap-3 px-4 py-3.5",
                          campo.estado === "no_detectado" && "bg-red-50/30",
                          campo.estado === "dudoso" && "bg-amber-50/40",
                          isEditing && "ring-2 ring-inset ring-primary/30",
                        )}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold text-foreground">
                            {campo.etiqueta}
                          </span>
                          <Badge variant={statusMeta.variant}>
                            {statusMeta.label}
                            {campo.confianza !== null && !campo.editadoManualmente
                              ? ` · ${Math.round(campo.confianza * 100)}%`
                              : ""}
                          </Badge>
                          {campo.evidencia?.pagina ? (
                            <span className="text-[11px] text-muted-foreground">
                              Pág. {campo.evidencia.pagina}
                            </span>
                          ) : null}
                        </div>

                        {isEditing ? (
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                            <input
                              type="text"
                              value={draftValue}
                              onChange={(e) => setDraftValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  e.preventDefault();
                                  commitEditing(activeDoc.documentoId, campo.clave);
                                } else if (e.key === "Escape") {
                                  e.preventDefault();
                                  cancelEditing();
                                }
                              }}
                              placeholder={getPlaceholder(
                                activeDoc.tipoSeleccionado,
                                campo.clave,
                              )}
                              autoFocus
                              className="w-full flex-1 rounded-lg border border-primary/50 bg-white px-3 py-1.5 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                            />
                            <div className="flex items-center gap-1.5">
                              <Button
                                type="button"
                                size="sm"
                                onClick={() =>
                                  commitEditing(activeDoc.documentoId, campo.clave)
                                }
                              >
                                <Check className="h-3.5 w-3.5" />
                                Guardar
                              </Button>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={cancelEditing}
                              >
                                <X className="h-3.5 w-3.5" />
                                Cancelar
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                            <div className="space-y-1">
                              {campo.valorActual ? (
                                <p className="text-sm font-medium text-foreground">
                                  {campo.valorActual}
                                </p>
                              ) : (
                                <p className="flex items-center gap-1.5 text-xs italic text-muted-foreground">
                                  <AlertCircle className="h-3.5 w-3.5 text-primary/70" />
                                  Sin dato detectado. Complétalo viendo el
                                  documento al lado.
                                </p>
                              )}
                              {campo.editadoManualmente && (
                                <p className="text-[11px] text-muted-foreground">
                                  Valor original IA:{" "}
                                  <span className="font-medium text-foreground">
                                    {campo.valorDetectado ?? "Sin detectar"}
                                  </span>
                                </p>
                              )}
                            </div>
                            <div className="flex shrink-0 items-center gap-1.5">
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  startEditing(activeDoc.documentoId, campo)
                                }
                              >
                                <Pencil className="h-3.5 w-3.5" />
                                {campo.valorActual ? "Editar" : "Completar"}
                              </Button>
                              {campo.editadoManualmente && (
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  onClick={() =>
                                    onRestoreField(activeDoc.documentoId, campo.clave)
                                  }
                                >
                                  <RotateCcw className="h-3.5 w-3.5" />
                                  Restaurar
                                </Button>
                              )}
                            </div>
                          </div>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>

            {showViewer && (
              <div ref={viewerRef} className="min-w-0 xl:sticky xl:top-6">
                <DocumentViewerPane
                  target={{
                    documentoId: activeDoc.documentoId,
                    nombreArchivo: activeDoc.nombreArchivo,
                    tipoDocumento: activeDoc.tipoSeleccionado,
                    file: activeFile,
                    page: resolvedId === activeId ? viewerPage : undefined,
                  }}
                  viewportClassName="min-h-[420px] xl:max-h-[calc(100vh-8rem)]"
                />
              </div>
            )}
          </div>
        )}

        {showJsonPreview && (
          <div className="rounded-xl border border-border bg-secondary/30 p-4">
            <div className="mb-2 flex items-center justify-between gap-2">
              <p className="text-xs font-semibold text-secondary-foreground">
                Payload JSON listo para PATCH /api/v1/expedientes/{"{id}"}
                /revalidar
              </p>
              <Badge variant="outline" className="border-border bg-white">
                Contrato Zod
              </Badge>
            </div>
            <pre className="max-h-64 overflow-auto rounded-lg border border-border bg-white p-3 font-mono text-xs text-foreground">
              {JSON.stringify(payloadPreview, null, 2)}
            </pre>
          </div>
        )}

        <div className="flex flex-col gap-3 rounded-xl border border-border bg-secondary/40 px-4 py-3.5">
          <AgentThoughtLine
            statuses={
              isConfirming || confirmedAt
                ? agentStatuses
                : agentStatuses.map(() => "pending")
            }
            working={isConfirming}
            elapsedSec={
              isConfirming || confirmedAt ? analysisElapsedSec : null
            }
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="max-w-xl text-xs leading-relaxed text-muted-foreground">
            {isConfirming
              ? "Los pasos de arriba son el rastro local. Cuando el backend esté listo, cada agente irá agregando el suyo."
              : confirmedAt
                ? `Última confirmación local: ${confirmedAt}. Puedes reabrir el rastro o ver el detalle en Resultado.`
                : "Puedes validar tal cual o corregir antes. Al conectar el backend, este botón re-ejecuta reglas, cruces y dictamen sin repetir el OCR."}
          </p>
          <Button
            type="button"
            disabled={isConfirming}
            onClick={onConfirmForValidation}
          >
            <CheckCircle2 className="h-4 w-4" />
            {isConfirming
              ? "Confirmando..."
              : confirmedAt
                ? "Revalidar ajustes"
                : "Confirmar campos y continuar"}
          </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
