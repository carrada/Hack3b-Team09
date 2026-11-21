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
import { CargaView } from "@/components/workspace/carga-view";
import {
  DocumentPreviewDrawer,
  type PreviewDocumentTarget,
} from "@/components/workspace/document-preview-drawer";
import { EntryLoader } from "@/components/workspace/entry-loader";
import { ExpedienteGuideView } from "@/components/workspace/expediente-guide-view";
import { InicioPitchView } from "@/components/workspace/inicio-pitch-view";
import { ResultadoView } from "@/components/workspace/resultado-view";
import { ApiClientError, analizarExpediente } from "@/lib/api";
import { env } from "@/lib/config/env";
import type { AnalisisEstado, TipoDocumento, UsoRequerido } from "@/lib/contracts";
import { useBackendHealth } from "@/hooks/use-expedientes";

type ViewId = "inicio" | "expediente" | "carga" | "resultado";

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
      "Recepción, cuatro especialistas y el Validador cruzado. El Dictamen cierra: verifica citas, calcula la confianza y recomienda.",
  },
  expediente: {
    badge: "Paso 02 · Qué se evalúa",
    title: "Estructura del expediente y reglas cruzadas",
    subtitle:
      "Cuatro tipos documentales. Los campos salen de config/reglas y el Validador cruzado compara dirección, propietario, superficie y número oficial.",
  },
  carga: {
    badge: "Paso 03 · Ingesta",
    title: "Carga para el grafo",
    subtitle:
      "Sube los archivos y elige tienda o CEDIS. Recepción clasifica por contenido; no hay edición de campos antes del análisis.",
  },
  resultado: {
    badge: "Paso 04 · Dictamen y evidencia",
    title: "Resultado del grafo",
    subtitle:
      "Recomendación, confianza, citas verificadas, cruces y la bitácora que escribieron los agentes.",
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

function tipoPreview(nombre: string): TipoDocumento {
  const lower = nombre.toLowerCase();
  if (lower.includes("predial")) return "predial";
  if (lower.includes("alineamiento") || lower.includes("numero")) {
    return "alineamiento_numero_oficial";
  }
  if (lower.includes("suelo") || lower.includes("uso")) return "uso_de_suelo";
  if (lower.includes("escritura")) return "escritura";
  return "otro";
}

export function AppShell() {
  const [activeView, setActiveView] = useState<ViewId>("inicio");
  const [menuSyncVersion, setMenuSyncVersion] = useState(0);
  const [files, setFiles] = useState<File[]>([]);
  const [uso, setUso] = useState<UsoRequerido>("tienda");
  const [analisis, setAnalisis] = useState<AnalisisEstado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [elapsedSec, setElapsedSec] = useState<number | null>(null);
  const [preview, setPreview] = useState<PreviewDocumentTarget | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const health = useBackendHealth();

  const meta = VIEW_META[activeView];

  useEffect(() => {
    if (!isRunning) return;
    const id = window.setInterval(() => {
      const startedAt = startedAtRef.current;
      if (startedAt === null) return;
      setElapsedSec((performance.now() - startedAt) / 1000);
    }, 250);
    return () => window.clearInterval(id);
  }, [isRunning]);

  const navigateProgrammatically = (targetView: ViewId) => {
    setActiveView(targetView);
    setMenuSyncVersion((prev) => prev + 1);
  };

  const handleSelect = (value: string) => {
    if (isViewId(value)) setActiveView(value);
  };

  const resetAnalisis = () => {
    setAnalisis(null);
    setError(null);
    setElapsedSec(null);
    setPreview(null);
  };

  const handleFilesAdded = (newFiles: File[]) => {
    if (newFiles.length === 0) return;
    setFiles((prev) => [...prev, ...newFiles]);
    resetAnalisis();
  };

  const handleRemoveByIndex = (index: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== index));
    resetAnalisis();
  };

  const handleClearFiles = () => {
    setFiles([]);
    resetAnalisis();
  };

  const handleAnalizar = async () => {
    if (files.length === 0 || isRunning) return;
    setError(null);
    setAnalisis(null);
    setIsRunning(true);
    const startedAt = performance.now();
    startedAtRef.current = startedAt;
    setElapsedSec(0);
    try {
      const resultado = await analizarExpediente({ uso, archivos: files });
      setAnalisis(resultado);
      setElapsedSec((performance.now() - startedAt) / 1000);
      navigateProgrammatically("resultado");
    } catch (err) {
      const message =
        err instanceof ApiClientError
          ? err.message
          : "No se pudo analizar el expediente.";
      setError(message);
    } finally {
      setIsRunning(false);
      startedAtRef.current = null;
    }
  };

  const handlePreviewDoc = (nombreArchivo: string, pagina?: number) => {
    const file = files.find((item) => item.name === nombreArchivo);
    setPreview({
      documentoId: nombreArchivo,
      nombreArchivo,
      tipoDocumento: tipoPreview(nombreArchivo),
      file,
      page: pagina,
    });
  };

  const salud =
    env.useMocks
      ? "Modo mock activo: el análisis no inventa un dictamen."
      : health.data?.status === "degraded"
        ? health.data.detalle || "Backend degradado: el modelo no está disponible."
        : health.data?.status === "ok"
          ? "Grafo disponible."
          : health.isError
            ? "Sin conexión con el backend."
            : "Comprobando el backend…";

  return (
    <div className="min-h-screen bg-white text-foreground flex flex-col md:flex-row">
      <EntryLoader />
      <DocumentPreviewDrawer target={preview} onClose={() => setPreview(null)} />

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
              Grafo
            </p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              6 agentes, del 01 Recepción al 06 Validador cruzado. El Dictamen
              cierra.
            </p>
            <div className="mt-3 flex flex-col gap-1.5 text-xs font-medium text-secondary-foreground">
              <div className="flex items-center justify-between">
                <span>Archivos en sesión</span>
                <span className="rounded-full bg-white px-2.5 py-0.5 text-primary border border-border">
                  {files.length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Uso</span>
                <span className="rounded-full bg-white px-2.5 py-0.5 text-primary border border-border">
                  {uso}
                </span>
              </div>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              {salud}
            </p>
          </div>
        </div>
      </aside>

      <main className="flex-1 bg-white">
        <header className="border-b border-border bg-white px-6 py-6 md:px-10">
          <div className="mx-auto max-w-5xl space-y-1.5">
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
        </header>

        <div className="mx-auto max-w-5xl px-6 py-8 md:px-10">
          {activeView === "inicio" && (
            <InicioPitchView
              onStartDemo={() => navigateProgrammatically("carga")}
            />
          )}
          {activeView === "expediente" && <ExpedienteGuideView />}
          {activeView === "carga" && (
            <CargaView
              files={files}
              uso={uso}
              isRunning={isRunning}
              error={error}
              elapsedSec={elapsedSec}
              onUsoChange={setUso}
              onFilesAdded={handleFilesAdded}
              onRemoveByIndex={handleRemoveByIndex}
              onClear={handleClearFiles}
              onAnalizar={() => {
                void handleAnalizar();
              }}
            />
          )}
          {activeView === "resultado" && (
            <ResultadoView
              analisis={analisis}
              isRunning={isRunning}
              error={error}
              elapsedSec={elapsedSec}
              onPreviewDoc={handlePreviewDoc}
            />
          )}
        </div>
      </main>
    </div>
  );
}
