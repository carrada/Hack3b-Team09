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
import { EntryLoader } from "@/components/workspace/entry-loader";
import { ExpedienteGuideView } from "@/components/workspace/expediente-guide-view";
import { InicioPitchView } from "@/components/workspace/inicio-pitch-view";
import { ResultadoView } from "@/components/workspace/resultado-view";
import { ApiClientError, analizarExpediente } from "@/lib/api";
import { env } from "@/lib/config/env";
import type { AnalisisEstado, UsoRequerido } from "@/lib/contracts";
import { claveManual } from "@/lib/workspace/campos-documento";
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
      "Sube los PDF, detecta los campos según el tipo de documento y completa a mano lo que falte, con el archivo a la vista.",
  },
  resultado: {
    badge: "Paso 04 · Dictamen",
    title: "Resultado del grafo",
    subtitle:
      "Primero la recomendación. Después documentos, cruces y la bitácora.",
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
  const [files, setFiles] = useState<File[]>([]);
  const [uso, setUso] = useState<UsoRequerido>("tienda");
  const [analisis, setAnalisis] = useState<AnalisisEstado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [elapsedSec, setElapsedSec] = useState<number | null>(null);
  const [manuales, setManuales] = useState<Record<string, string>>({});
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
    setManuales({});
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
      setManuales({});
      setElapsedSec((performance.now() - startedAt) / 1000);
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

  const handleManualChange = (documentoId: string, nombre: string, valor: string) => {
    const clave = claveManual(documentoId, nombre);
    setManuales((prev) => {
      const next = { ...prev };
      if (!valor.trim()) delete next[clave];
      else next[clave] = valor;
      return next;
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
                <span>Capturas manuales</span>
                <span className="rounded-full bg-white px-2.5 py-0.5 text-primary border border-border">
                  {Object.keys(manuales).length}
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
          <div className={`mx-auto space-y-1.5 ${activeView === "inicio" || activeView === "expediente" ? "max-w-5xl" : "max-w-7xl"}`}>
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

        <div className={`mx-auto px-6 py-8 md:px-10 ${activeView === "inicio" || activeView === "expediente" ? "max-w-5xl" : "max-w-7xl"}`}>
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
              analisis={analisis}
              manuales={manuales}
              onAnalizar={() => {
                void handleAnalizar();
              }}
              onManualChange={handleManualChange}
              onVerDictamen={() => navigateProgrammatically("resultado")}
            />
          )}
          {activeView === "resultado" && (
            <ResultadoView
              analisis={analisis}
              files={files}
              manuales={manuales}
              isRunning={isRunning}
              error={error}
              elapsedSec={elapsedSec}
            />
          )}
        </div>
      </main>
    </div>
  );
}
