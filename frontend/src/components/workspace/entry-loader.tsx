"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import LatticeLoader from "@/components/ui/LatticeLoader";

type LoaderPhase = "working" | "done" | "fading" | "hidden";

export function EntryLoader() {
  const [phase, setPhase] = useState<LoaderPhase>("working");

  useEffect(() => {
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const workMs = prefersReducedMotion ? 220 : 620;
    const doneMs = prefersReducedMotion ? 160 : 340;
    const fadeMs = 220;

    const doneTimer = window.setTimeout(() => setPhase("done"), workMs);
    const fadeTimer = window.setTimeout(
      () => setPhase("fading"),
      workMs + doneMs,
    );
    const hideTimer = window.setTimeout(
      () => setPhase("hidden"),
      workMs + doneMs + fadeMs,
    );

    return () => {
      window.clearTimeout(doneTimer);
      window.clearTimeout(fadeTimer);
      window.clearTimeout(hideTimer);
    };
  }, []);

  if (phase === "hidden") return null;

  return (
    <div
      aria-label="Cargando aplicación"
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center gap-5 bg-white transition-opacity duration-200 ${
        phase === "fading" ? "pointer-events-none opacity-0" : "opacity-100"
      }`}
    >
      <div className="flex flex-col items-center gap-3">
        <Image
          src="/logo-3b.png"
          alt="Tiendas 3B"
          width={64}
          height={64}
          priority
          className="h-16 w-16 object-contain"
        />
        <p className="text-sm font-semibold tracking-tight text-foreground">
          Expedientes 3B
        </p>
      </div>

      <LatticeLoader
        status={phase === "working" ? "working" : "done"}
        label="Iniciando entorno"
        doneLabel="Listo en"
        errorLabel="Error tras"
        pattern="orbit"
        grid={3}
        shape="round"
        color="#E10600"
        doneColor="#22c55e"
        errorColor="#ef4444"
        cellSize={7}
        gap={3}
        fontSize={14}
        step={75}
        idleOpacity={0.18}
        glow={false}
        glowColor=""
        showTimer
      />
    </div>
  );
}
