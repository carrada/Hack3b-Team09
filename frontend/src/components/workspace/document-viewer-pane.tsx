"use client";

import { useEffect, useMemo, type ReactNode } from "react";
import { ExternalLink, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TIPO_DOCUMENTO_LABELS, type TipoDocumento } from "@/lib/contracts";
import { cn } from "@/lib/utils";

export interface DocumentViewerTarget {
  documentoId: string;
  nombreArchivo: string;
  tipoDocumento: TipoDocumento;
  file?: File;
  url?: string;
  page?: number;
}

export function DocumentViewerPane({
  target,
  headerActions,
  className,
  viewportClassName,
}: {
  target: DocumentViewerTarget;
  headerActions?: ReactNode;
  className?: string;
  viewportClassName?: string;
}) {
  const objectUrl = useMemo(() => {
    if (!target.file || typeof URL === "undefined") return null;
    return URL.createObjectURL(target.file);
  }, [target.file]);

  useEffect(() => {
    if (!objectUrl) return undefined;
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [objectUrl]);

  const baseUrl = objectUrl ?? target.url ?? null;
  const mime = target.file?.type?.toLowerCase() ?? "";
  const lowerName = target.nombreArchivo.toLowerCase();
  const isImage =
    mime.startsWith("image/") || /\.(png|jpe?g|webp|gif)$/i.test(lowerName);
  const isPdf = mime === "application/pdf" || lowerName.endsWith(".pdf");

  const resolvedUrl =
    baseUrl && isPdf && target.page && target.page > 0
      ? `${baseUrl}#page=${target.page}`
      : baseUrl;

  return (
    <div
      className={cn(
        "flex flex-col overflow-hidden rounded-xl border border-border bg-white",
        className,
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-secondary/40 px-4 py-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <FileText className="h-4 w-4 shrink-0 text-primary" />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">
              {target.nombreArchivo}
            </p>
            <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
              <Badge variant="secondary" className="border-border text-primary">
                {TIPO_DOCUMENTO_LABELS[target.tipoDocumento]}
              </Badge>
              {target.page && target.page > 0 && (
                <Badge variant="outline" className="border-border bg-white">
                  Pág. {target.page}
                </Badge>
              )}
              <span className="text-[11px] text-muted-foreground">
                Vista local directa
              </span>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          {resolvedUrl && (
            <a
              href={resolvedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-white px-2.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Abrir
            </a>
          )}
          {headerActions}
        </div>
      </div>

      <div
        className={cn(
          "flex-1 overflow-auto bg-secondary/20 p-3",
          viewportClassName,
        )}
      >
        {!resolvedUrl ? (
          <div className="flex h-full min-h-[360px] items-center justify-center rounded-lg border border-dashed border-border bg-white p-6 text-center text-sm text-muted-foreground">
            No hay archivo disponible para previsualizar en esta sesión.
          </div>
        ) : isPdf ? (
          <iframe
            key={resolvedUrl}
            src={resolvedUrl}
            title={target.nombreArchivo}
            className="h-full min-h-[520px] w-full rounded-lg border border-border bg-white"
          />
        ) : isImage ? (
          <div className="flex min-h-[420px] items-center justify-center rounded-lg border border-border bg-white p-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={resolvedUrl}
              alt={target.nombreArchivo}
              className="max-h-[72vh] w-auto rounded-md object-contain"
            />
          </div>
        ) : (
          <div className="flex h-full min-h-[360px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-white p-6 text-center">
            <FileText className="h-8 w-8 text-primary" />
            <p className="text-sm font-medium text-foreground">
              Vista embebida no disponible para este formato
            </p>
            <p className="max-w-sm text-xs text-muted-foreground">
              Usa el botón Abrir para revisar el archivo directamente en una
              nueva pestaña del navegador.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
