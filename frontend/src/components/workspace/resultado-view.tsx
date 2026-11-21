"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  Copy,
  Eye,
  FileSearch,
  GitCompareArrows,
  PencilLine,
  Play,
  Printer,
  RotateCw,
  ShieldAlert,
  Wrench,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import StatusMark, { type StatusMarkState } from "@/components/ui/StatusMark";
import { AgentThoughtLine } from "@/components/workspace/agent-thought-line";
import {
  DOCUMENTOS_MINIMOS_RETO_1,
  TIPO_DOCUMENTO_LABELS,
  type DocumentoRevision,
} from "@/lib/contracts";
import { AGENT_PIPELINE_STEPS } from "@/lib/workspace/agent-pipeline";
import { contarResumenRevision } from "@/lib/workspace/review-helpers";

export { AGENT_PIPELINE_STEPS };

const STATUS_TEXT: Record<StatusMarkState, string> = {
  pending: "En espera",
  running: "Ejecutando",
  done: "Completado",
  failed: "Con error",
  cancelled: "Omitido",
};

function buildFollowupRequestText(documentos: DocumentoRevision[]): string {
  const tiposPresentes = new Set(documentos.map((doc) => doc.tipoSeleccionado));
  const faltantes = DOCUMENTOS_MINIMOS_RETO_1.filter(
    (tipo) => !tiposPresentes.has(tipo),
  );
  const camposSinDato = documentos.flatMap((doc) =>
    doc.campos
      .filter((campo) => !campo.valorActual)
      .map((campo) => `${TIPO_DOCUMENTO_LABELS[doc.tipoSeleccionado]} · ${campo.etiqueta}`),
  );
  const ediciones = documentos.flatMap((doc) =>
    doc.campos
      .filter((campo) => campo.editadoManualmente)
      .map(
        (campo) =>
          `${TIPO_DOCUMENTO_LABELS[doc.tipoSeleccionado]} · ${campo.etiqueta}: ${campo.valorActual ?? "Sin valor"}`,
      ),
  );

  const lines: string[] = [
    "Solicitud de seguimiento · Expediente Inmobiliario (Tiendas 3B)",
    "",
  ];

  if (faltantes.length > 0) {
    lines.push("Documentos mínimos faltantes (subsanables):");
    for (const tipo of faltantes) {
      lines.push(`- ${TIPO_DOCUMENTO_LABELS[tipo]}`);
    }
    lines.push("");
  }

  if (camposSinDato.length > 0) {
    lines.push("Datos pendientes de confirmar o completar:");
    for (const item of camposSinDato.slice(0, 12)) {
      lines.push(`- ${item}`);
    }
    if (camposSinDato.length > 12) {
      lines.push(`- ... y ${camposSinDato.length - 12} campo(s) adicional(es)`);
    }
    lines.push("");
  }

  if (ediciones.length > 0) {
    lines.push("Ajustes capturados manualmente para verificación:");
    for (const item of ediciones) {
      lines.push(`- ${item}`);
    }
    lines.push("");
  }

  if (faltantes.length === 0 && camposSinDato.length === 0) {
    lines.push(
      "Expediente completo en sesión (4/4 tipos documentales). Listo para validación final del equipo legal.",
    );
  }

  return lines.join("\n").trim();
}

export function ResultadoView({
  documentos,
  confirmedAt,
  isRunningAgents,
  lastRunDurationSec,
  analysisElapsedSec,
  agentStatuses,
  onRunPipelinePreview,
  onRevalidateOnly,
  onPreviewDoc,
}: {
  documentos: DocumentoRevision[];
  confirmedAt: string | null;
  isRunningAgents: boolean;
  lastRunDurationSec: number | null;
  analysisElapsedSec: number | null;
  agentStatuses: readonly StatusMarkState[];
  onRunPipelinePreview: () => void;
  onRevalidateOnly: () => void;
  onPreviewDoc: (documentoId: string) => void;
}) {
  const [copied, setCopied] = useState(false);

  const summary = contarResumenRevision(documentos);
  const tiposPresentes = new Set(documentos.map((doc) => doc.tipoSeleccionado));
  const faltantes = DOCUMENTOS_MINIMOS_RETO_1.filter(
    (tipo) => !tiposPresentes.has(tipo),
  );

  const manualEdits = documentos.flatMap((doc) =>
    doc.campos
      .filter((campo) => campo.editadoManualmente)
      .map((campo) => ({
        documentoId: doc.documentoId,
        nombreArchivo: doc.nombreArchivo,
        tipoDocumento: doc.tipoSeleccionado,
        campo,
      })),
  );

  const completedAgents = agentStatuses.filter((s) => s === "done").length;

  const handleCopyFollowup = async () => {
    const text = buildFollowupRequestText(documentos);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2200);
    } catch {
      setCopied(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-white px-4 py-3">
          <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            <Clock className="h-3.5 w-3.5 text-primary" />
            Tiempo de análisis
          </p>
          <p className="mt-1 text-lg font-semibold text-foreground">
            {isRunningAgents
              ? `${(analysisElapsedSec ?? 0).toFixed(1)} s`
              : lastRunDurationSec !== null
                ? `${lastRunDurationSec.toFixed(1)} s`
                : "Sin ejecutar"}
          </p>
        </div>

        <div className="rounded-xl border border-border bg-white px-4 py-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Documentos mínimos
          </p>
          <p className="mt-1 text-lg font-semibold text-foreground">
            {DOCUMENTOS_MINIMOS_RETO_1.length - faltantes.length} / 4
          </p>
        </div>

        <div className="rounded-xl border border-border bg-white px-4 py-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Campos con dato
          </p>
          <p className="mt-1 text-lg font-semibold text-foreground">
            {summary.camposCompletos} / {summary.totalCampos}
          </p>
        </div>

        <div className="rounded-xl border border-border bg-white px-4 py-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Correcciones manuales
          </p>
          <p className="mt-1 text-lg font-semibold text-foreground">
            {summary.camposEditados}
          </p>
        </div>
      </div>

      <Card className="border-primary/30 bg-white shadow-xs no-print">
        <CardContent className="flex flex-wrap items-start justify-between gap-4 py-4">
          <AgentThoughtLine
            statuses={agentStatuses}
            working={isRunningAgents}
            elapsedSec={isRunningAgents ? analysisElapsedSec : lastRunDurationSec}
          />
          <Badge variant="secondary" className="border-border text-primary">
            Agentes completados: {completedAgents}/6
          </Badge>
        </CardContent>
      </Card>

      <Card className="border-primary/25 bg-secondary/40">
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="text-lg text-secondary-foreground">
                Dictamen inicial y cierre de acción
              </CardTitle>
              <CardDescription>
                Vista de Nivel 1: semáforo claro y acciones directas para gestor
                y equipo legal.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2 no-print">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleCopyFollowup}
                className="bg-white"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                    Solicitud copiada
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    Copiar pendientes (Gestor)
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handlePrint}
                className="bg-white"
              >
                <Printer className="h-3.5 w-3.5" />
                Imprimir / PDF (Legal)
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <span>
              Estado del expediente:{" "}
              <span className="font-semibold text-foreground">
                {isRunningAgents
                  ? `Procesando (${completedAgents}/6 agentes)`
                  : confirmedAt
                    ? `Confirmado a las ${confirmedAt} · listo para backend`
                    : "En espera de conexión con backend"}
              </span>
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-emerald-200 bg-white p-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Cumple
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Expediente completo, reglas aprobadas y sin inconsistencias
                críticas entre documentos.
              </p>
            </div>
            <div className="rounded-lg border border-amber-200 bg-white p-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-700">
                <AlertTriangle className="h-3.5 w-3.5" />
                Requiere revisión
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Observaciones subsanables o condicionantes: no descarta un local
                viable antes de validarlo.
              </p>
            </div>
            <div className="rounded-lg border border-red-200 bg-white p-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-red-700">
                <XCircle className="h-3.5 w-3.5" />
                No cumple
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Existe al menos un hallazgo bloqueante comprobado con evidencia
                documental.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-red-200 bg-white">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2 text-base text-red-800">
                <ShieldAlert className="h-4 w-4 text-primary" />
                Hallazgos bloqueantes
              </CardTitle>
              <Badge variant="destructive">Impiden continuar</Badge>
            </div>
            <CardDescription>
              Riesgos legales graves (ej. giro prohibido o inmuebles distintos).
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs leading-relaxed text-muted-foreground">
            Sin bloqueantes reportados todavía. Al conectar el backend de
            LangChain, únicamente los impedimentos críticos aparecerán aquí con
            cita directa al documento.
          </CardContent>
        </Card>

        <Card className="border-amber-200 bg-white">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2 text-base text-amber-900">
                <Wrench className="h-4 w-4 text-amber-600" />
                Observaciones subsanables
              </CardTitle>
              <Badge variant="warning">Se pueden corregir</Badge>
            </div>
            <CardDescription>
              Faltantes o aclaraciones que el gestor puede solicitar sin
              descartar el local.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-muted-foreground">
            {faltantes.length === 0 && summary.camposPorRevisar === 0 ? (
              <p>
                No hay pendientes subsanables detectados en la sesión local.
              </p>
            ) : (
              <ul className="space-y-1.5">
                {faltantes.map((tipo) => (
                  <li key={tipo} className="flex items-start gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    <span>
                      Solicitar documento faltante:{" "}
                      <strong className="font-medium text-foreground">
                        {TIPO_DOCUMENTO_LABELS[tipo]}
                      </strong>
                    </span>
                  </li>
                ))}
                {summary.camposPorRevisar > 0 && (
                  <li className="flex items-start gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    <span>
                      {summary.camposPorRevisar} campo(s) sin dato o por
                      confirmar en la pestaña{" "}
                      <strong className="font-medium text-foreground">
                        Carga
                      </strong>
                      .
                    </span>
                  </li>
                )}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {manualEdits.length > 0 && (
        <Card className="border-border bg-white">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <PencilLine className="h-4 w-4 text-primary" />
                Auditoría de correcciones manuales ({manualEdits.length})
              </CardTitle>
              <Badge variant="secondary" className="border-border text-primary">
                Trazabilidad Human-in-the-Loop
              </Badge>
            </div>
            <CardDescription>
              El equipo legal siempre distingue qué valor extrajo la IA y qué
              valor corrigió el usuario antes de validar.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border rounded-lg border border-border">
              {manualEdits.map(
                ({ documentoId, nombreArchivo, tipoDocumento, campo }) => (
                  <li
                    key={`${documentoId}-${campo.clave}`}
                    className="flex flex-col gap-2 px-4 py-3 text-xs sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="font-semibold text-foreground">
                        {campo.etiqueta}{" "}
                        <span className="font-normal text-muted-foreground">
                          · {TIPO_DOCUMENTO_LABELS[tipoDocumento]} (
                          {nombreArchivo})
                        </span>
                      </p>
                      <p className="mt-0.5 text-muted-foreground">
                        IA: {campo.valorDetectado ?? "Sin detectar"} → Usuario:{" "}
                        <span className="font-semibold text-foreground">
                          {campo.valorActual ?? "Vacío"}
                        </span>
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => onPreviewDoc(documentoId)}
                      className="h-7 w-fit text-xs no-print"
                    >
                      <Eye className="h-3.5 w-3.5 text-primary" />
                      Comprobar archivo
                    </Button>
                  </li>
                ),
              )}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-border bg-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ClipboardCheck className="h-4 w-4 text-primary" />
              Nivel 2 · Completitud documental (4/4)
            </CardTitle>
            <CardDescription>
              Abre cualquier archivo cargado para verificar evidencia al
              instante.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2.5">
              {DOCUMENTOS_MINIMOS_RETO_1.map((tipo) => {
                const matchedDoc = documentos.find(
                  (doc) => doc.tipoSeleccionado === tipo,
                );
                const presente = Boolean(matchedDoc);
                const status: StatusMarkState = presente
                  ? "done"
                  : confirmedAt
                    ? "failed"
                    : "pending";
                return (
                  <li
                    key={tipo}
                    className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2"
                  >
                    <StatusMark
                      status={status}
                      label={TIPO_DOCUMENTO_LABELS[tipo]}
                      color="#7A0704"
                      doneColor="#22c55e"
                      errorColor="#E10600"
                      size={18}
                      fontSize={13}
                      strike={false}
                    />
                    {matchedDoc ? (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => onPreviewDoc(matchedDoc.documentoId)}
                        className="h-7 px-2 text-xs text-primary hover:bg-secondary no-print"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        Ver
                      </Button>
                    ) : (
                      <span className="text-[11px] font-medium text-muted-foreground">
                        {confirmedAt ? "Faltante" : "Pendiente"}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>

        <Card className="border-border bg-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GitCompareArrows className="h-4 w-4 text-primary" />
              Nivel 2 · Inconsistencias cruzadas
            </CardTitle>
            <CardDescription>
              Comparativa lado a lado entre documentos del mismo inmueble.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs leading-relaxed text-muted-foreground">
            Al conectarse con el backend de LangChain, cada discrepancia de
            dirección, propietario, superficie, número oficial o clave predial
            aparecerá aquí con qué documentos la presentan, qué valor encontró
            el sistema en cada uno, cita de página/fragmento y acceso directo al
            visor del PDF.
          </CardContent>
        </Card>
      </div>

      <Card className="border-border bg-white">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2 text-base">
                <Eye className="h-4 w-4 text-primary" />
                Nivel 3 · Progreso y trazabilidad de los 6 agentes
              </CardTitle>
              <CardDescription>
                Estado individual de cada agente. Si editas campos manualmente,
                solo se re-ejecutan los Agentes 03–06 sin repetir lectura OCR.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2 no-print">
              <Badge
                variant="secondary"
                className="border-border text-secondary-foreground"
              >
                <FileSearch className="h-3.5 w-3.5" />
                {completedAgents}/6 completados
              </Badge>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isRunningAgents}
                onClick={onRunPipelinePreview}
              >
                <Play className="h-3.5 w-3.5" />
                Probar flujo 01–06
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={isRunningAgents}
                onClick={onRevalidateOnly}
              >
                <RotateCw className="h-3.5 w-3.5" />
                Revalidar 03–06
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {AGENT_PIPELINE_STEPS.map((agent, index) => {
              const status = agentStatuses[index] ?? "pending";
              return (
                <div
                  key={agent.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border bg-white px-4 py-3"
                >
                  <StatusMark
                    status={status}
                    label={agent.label}
                    color="#E10600"
                    doneColor="#22c55e"
                    errorColor="#E10600"
                    size={20}
                    fontSize={13}
                    strike={false}
                  />
                  <span className="shrink-0 text-[11px] font-medium text-muted-foreground">
                    {STATUS_TEXT[status]}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
