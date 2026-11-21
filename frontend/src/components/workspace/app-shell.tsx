"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import {
  CheckmarkCircle02Icon,
  CloudUploadIcon,
  Folder01Icon,
  Home01Icon,
} from "@hugeicons/core-free-icons";
import BranchedMenu, {
  type BranchedMenuSectionItem,
} from "@/components/menu/BranchedMenu";
import { Badge } from "@/components/ui/badge";
import type { StatusMarkState } from "@/components/ui/StatusMark";
import { CargaView } from "@/components/workspace/carga-view";
import {
  DocumentPreviewDrawer,
  type PreviewDocumentTarget,
} from "@/components/workspace/document-preview-drawer";
import { EntryLoader } from "@/components/workspace/entry-loader";
import { ExpedienteGuideView } from "@/components/workspace/expediente-guide-view";
import { InicioPitchView } from "@/components/workspace/inicio-pitch-view";
import { ResultadoView } from "@/components/workspace/resultado-view";
import type { DocumentoRevision, TipoDocumento } from "@/lib/contracts";
import { AGENT_PIPELINE_STEPS } from "@/lib/workspace/agent-pipeline";
import {
  actualizarCampoDocumento,
  cambiarTipoDocumentoRevision,
  contarResumenRevision,
  crearDocumentoRevisionDesdeArchivo,
  restaurarCampoDocumento,
} from "@/lib/workspace/review-helpers";

type ViewId = "inicio" | "expediente" | "carga" | "resultado";

interface UploadedEntry {
  file: File;
  revision: DocumentoRevision;
}

const INITIAL_AGENT_STATUSES: StatusMarkState[] = AGENT_PIPELINE_STEPS.map(
  () => "pending",
);

const MENU_ITEMS: BranchedMenuSectionItem[] = [
  {
    label: "General",
    children: [{ value: "inicio", label: "Inicio", icon: Home01Icon }],
  },
  {
    label: "Flujo",
    children: [
      { value: "expediente", label: "Expediente", icon: Folder01Icon },
      { value: "carga", label: "Carga", icon: CloudUploadIcon },
      { value: "resultado", label: "Resultado", icon: CheckmarkCircle02Icon },
    ],
  },
];

const VIEW_META: Record<
  ViewId,
  { badge: string; title: string; subtitle: string }
> = {
  inicio: {
    badge: "Reto 1 · Arquitectura de 6 Agentes",
    title: "Revisión inteligente de expedientes inmobiliarios",
    subtitle:
      "Sistema multiagente sobre LangChain diseñado para dar velocidad operativa al gestor y trazabilidad jurídica completa al equipo legal, sin ocultar cómo razona la IA.",
  },
  expediente: {
    badge: "Paso 02 · Qué se evalúa",
    title: "Estructura del expediente y reglas cruzadas",
    subtitle:
      "Guía clara de los 4 tipos documentales mínimos, los campos que se extraen de cada uno y las validaciones cruzadas que contrastan coherencia entre documentos.",
  },
  carga: {
    badge: "Paso 03 · Ingesta y revisión asistida",
    title: "Carga y ajuste opcional de campos",
    subtitle:
      "Sube uno o varios PDFs del inmueble y, si algún campo no se detecta bien, corrígelo opcionalmente conservando el rastro original de la IA.",
  },
  resultado: {
    badge: "Paso 04 · Dictamen y evidencia",
    title: "Resultado auditable del análisis",
    subtitle:
      "Lectura en 3 niveles: recomendación inicial con confianza, hallazgos bloqueantes vs subsanables, visor directo del PDF y traza abierta de los 6 agentes.",
  },
};

function isViewId(value: string): value is ViewId {
  return (
    value === "inicio" ||
    value === "expediente" ||
    value === "carga" ||
    value === "resultado"
  );
}

export function AppShell() {
  const [activeView, setActiveView] = useState<ViewId>("inicio");
  const [menuSyncVersion, setMenuSyncVersion] = useState(0);
  const [entries, setEntries] = useState<UploadedEntry[]>([]);
  const [confirmedAt, setConfirmedAt] = useState<string | null>(null);
  const [isRunningAgents, setIsRunningAgents] = useState(false);
  const [lastRunDurationSec, setLastRunDurationSec] = useState<number | null>(
    null,
  );
  const [analysisElapsedSec, setAnalysisElapsedSec] = useState<number | null>(
    null,
  );
  const runStartedAtRef = useRef<number | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<StatusMarkState[]>(
    INITIAL_AGENT_STATUSES,
  );
  const [previewDocId, setPreviewDocId] = useState<string | null>(null);
  const timersRef = useRef<number[]>([]);

  const meta = VIEW_META[activeView];
  const uploadedFiles = entries.map((entry) => entry.file);
  const reviewDocs = entries.map((entry) => entry.revision);
  const reviewSummary = contarResumenRevision(reviewDocs);

  const previewTarget: PreviewDocumentTarget | null = (() => {
    if (!previewDocId) return null;
    const match = entries.find(
      (entry) => entry.revision.documentoId === previewDocId,
    );
    if (!match) return null;
    return {
      documentoId: match.revision.documentoId,
      nombreArchivo: match.revision.nombreArchivo,
      tipoDocumento: match.revision.tipoSeleccionado,
      file: match.file,
    };
  })();

  const clearPipelineTimers = () => {
    for (const id of timersRef.current) {
      window.clearTimeout(id);
    }
    timersRef.current = [];
  };

  useEffect(() => {
    return () => clearPipelineTimers();
  }, []);

  useEffect(() => {
    if (!isRunningAgents) return;
    const id = window.setInterval(() => {
      const startedAt = runStartedAtRef.current;
      if (startedAt === null) return;
      setAnalysisElapsedSec((performance.now() - startedAt) / 1000);
    }, 100);
    return () => window.clearInterval(id);
  }, [isRunningAgents]);

  const navigateProgrammatically = (targetView: ViewId) => {
    setActiveView(targetView);
    setMenuSyncVersion((prev) => prev + 1);
  };

  const runAgentSequence = (startIndex: number) => {
    clearPipelineTimers();
    const startedAt = performance.now();
    runStartedAtRef.current = startedAt;
    setAnalysisElapsedSec(0);
    setIsRunningAgents(true);

    setAgentStatuses(
      AGENT_PIPELINE_STEPS.map((_, idx) =>
        idx < startIndex ? "done" : idx === startIndex ? "running" : "pending",
      ),
    );

    const stepDurationMs = 420;
    const totalSteps = AGENT_PIPELINE_STEPS.length - startIndex;

    for (let offset = 0; offset < totalSteps; offset++) {
      const currentIdx = startIndex + offset;
      const timerId = window.setTimeout(() => {
        setAgentStatuses((prev) =>
          prev.map((state, idx) => {
            if (idx === currentIdx) return "done";
            if (idx === currentIdx + 1) return "running";
            return state;
          }),
        );

        if (currentIdx === AGENT_PIPELINE_STEPS.length - 1) {
          const elapsed = (performance.now() - startedAt) / 1000;
          setIsRunningAgents(false);
          setAnalysisElapsedSec(elapsed);
          setLastRunDurationSec(elapsed);
          setConfirmedAt(
            new Date().toLocaleTimeString("es-MX", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            }),
          );
        }
      }, stepDurationMs * (offset + 1));

      timersRef.current.push(timerId);
    }
  };

  const resetRunState = () => {
    clearPipelineTimers();
    setIsRunningAgents(false);
    setLastRunDurationSec(null);
    setAnalysisElapsedSec(null);
    runStartedAtRef.current = null;
    setConfirmedAt(null);
    setAgentStatuses(INITIAL_AGENT_STATUSES);
  };

  const handleSelect = (value: string) => {
    if (isViewId(value)) {
      setActiveView(value);
    }
  };

  const handleFilesAdded = (newFiles: File[]) => {
    if (newFiles.length === 0) return;
    setEntries((prev) => [
      ...prev,
      ...newFiles.map((file, idx) => ({
        file,
        revision: crearDocumentoRevisionDesdeArchivo(file, prev.length + idx),
      })),
    ]);
    resetRunState();
  };

  const handleRemoveByIndex = (index: number) => {
    setEntries((prev) => {
      const removed = prev[index];
      if (removed && removed.revision.documentoId === previewDocId) {
        setPreviewDocId(null);
      }
      return prev.filter((_, idx) => idx !== index);
    });
    resetRunState();
  };

  const handleClearFiles = () => {
    setEntries([]);
    setPreviewDocId(null);
    resetRunState();
  };

  const handleChangeDocType = (documentoId: string, tipo: TipoDocumento) => {
    setEntries((prev) =>
      prev.map((entry) =>
        entry.revision.documentoId === documentoId
          ? {
              ...entry,
              revision: cambiarTipoDocumentoRevision(entry.revision, tipo),
            }
          : entry,
      ),
    );
    setConfirmedAt(null);
  };

  const handleSaveField = (
    documentoId: string,
    clave: string,
    valor: string,
  ) => {
    setEntries((prev) =>
      prev.map((entry) =>
        entry.revision.documentoId === documentoId
          ? {
              ...entry,
              revision: actualizarCampoDocumento(entry.revision, clave, valor),
            }
          : entry,
      ),
    );
    setConfirmedAt(null);
  };

  const handleRestoreField = (documentoId: string, clave: string) => {
    setEntries((prev) =>
      prev.map((entry) =>
        entry.revision.documentoId === documentoId
          ? {
              ...entry,
              revision: restaurarCampoDocumento(entry.revision, clave),
            }
          : entry,
      ),
    );
    setConfirmedAt(null);
  };

  const handleRemoveDoc = (documentoId: string) => {
    if (previewDocId === documentoId) {
      setPreviewDocId(null);
    }
    setEntries((prev) =>
      prev.filter((entry) => entry.revision.documentoId !== documentoId),
    );
    resetRunState();
  };

  const handleConfirmForValidation = () => {
    const startFromValidationOnly =
      agentStatuses[0] === "done" && agentStatuses[1] === "done";
    runAgentSequence(startFromValidationOnly ? 2 : 0);
  };

  return (
    <div className="min-h-screen bg-white text-foreground flex flex-col md:flex-row">
      <EntryLoader />
      <DocumentPreviewDrawer
        target={previewTarget}
        onClose={() => setPreviewDocId(null)}
      />

      <aside className="no-print w-full shrink-0 border-b border-border bg-white md:w-72 md:border-r md:border-b-0">
        <div className="flex h-full flex-col px-6 py-7">
          <div className="mb-8 flex items-center gap-3">
            <Image
              src="/logo-3b.png"
              alt="Tiendas 3B"
              width={42}
              height={42}
              priority
              className="h-10 w-10 shrink-0 object-contain"
            />
            <div>
              <p className="text-base font-semibold leading-tight text-foreground">
                Expedientes 3B
              </p>
              <p className="text-xs text-muted-foreground">
                Revisión legal multiagente
              </p>
            </div>
          </div>

          <div className="flex-1">
            <BranchedMenu
              key={`menu-${menuSyncVersion}`}
              items={MENU_ITEMS}
              defaultOpen={[0, 1]}
              defaultActive={activeView}
              onSelect={handleSelect}
              color="#7A0704"
              accentColor="#E10600"
              lineColor="#E8C6C5"
              width={232}
              rowHeight={38}
              fontSize={14}
            />
          </div>

          <div className="mt-8 rounded-xl border border-border bg-secondary/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-secondary-foreground">
              Pipeline listo
            </p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              6 agentes especializados · modo local listo para conectar al
              backend.
            </p>
            <div className="mt-3 flex flex-col gap-1.5 text-xs font-medium text-secondary-foreground">
              <div className="flex items-center justify-between">
                <span>Archivos en sesión</span>
                <span className="rounded-full bg-white px-2.5 py-0.5 text-primary border border-border">
                  {reviewDocs.length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Correcciones manuales</span>
                <span className="rounded-full bg-white px-2.5 py-0.5 text-primary border border-border">
                  {reviewSummary.camposEditados}
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <main className="flex-1 bg-white">
        <header className="border-b border-border bg-white px-6 py-6 md:px-10">
          <div
            className={`mx-auto flex flex-wrap items-start justify-between gap-4 ${
              activeView === "carga" && reviewDocs.length > 0
                ? "max-w-7xl"
                : "max-w-5xl"
            }`}
          >
            <div className="space-y-1.5">
              <Badge variant="secondary" className="border-border text-primary">
                {meta.badge}
              </Badge>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl">
                {meta.title}
              </h1>
              <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
                {meta.subtitle}
              </p>
            </div>
          </div>
        </header>

        <div
          className={`mx-auto px-6 py-8 md:px-10 ${
            activeView === "carga" && reviewDocs.length > 0
              ? "max-w-7xl"
              : "max-w-5xl"
          }`}
        >
          {activeView === "inicio" && (
            <InicioPitchView
              onStartDemo={() => navigateProgrammatically("carga")}
            />
          )}
          {activeView === "expediente" && <ExpedienteGuideView />}
          {activeView === "carga" && (
            <CargaView
              files={uploadedFiles}
              documentos={reviewDocs}
              confirmedAt={confirmedAt}
              isConfirming={isRunningAgents}
              onFilesAdded={handleFilesAdded}
              onRemoveByIndex={handleRemoveByIndex}
              onClear={handleClearFiles}
              onChangeDocType={handleChangeDocType}
              onSaveField={handleSaveField}
              onRestoreField={handleRestoreField}
              onRemoveDoc={handleRemoveDoc}
              onConfirmForValidation={handleConfirmForValidation}
              agentStatuses={agentStatuses}
              analysisElapsedSec={analysisElapsedSec}
            />
          )}
          {activeView === "resultado" && (
            <ResultadoView
              documentos={reviewDocs}
              confirmedAt={confirmedAt}
              isRunningAgents={isRunningAgents}
              lastRunDurationSec={lastRunDurationSec}
              analysisElapsedSec={analysisElapsedSec}
              agentStatuses={agentStatuses}
              onRunPipelinePreview={() => runAgentSequence(0)}
              onRevalidateOnly={() => runAgentSequence(2)}
              onPreviewDoc={setPreviewDocId}
            />
          )}
        </div>
      </main>
    </div>
  );
}
