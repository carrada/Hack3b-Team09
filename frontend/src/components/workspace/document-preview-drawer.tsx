"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DocumentViewerPane,
  type DocumentViewerTarget,
} from "@/components/workspace/document-viewer-pane";

export type PreviewDocumentTarget = DocumentViewerTarget;

export function DocumentPreviewDrawer({
  target,
  onClose,
}: {
  target: PreviewDocumentTarget | null;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!target) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [target, onClose]);

  if (!target) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-[1px] print:hidden"
      role="dialog"
      aria-modal="true"
      aria-label={`Vista previa de ${target.nombreArchivo}`}
      onClick={onClose}
    >
      <div
        className="flex h-full w-full max-w-3xl flex-col bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <DocumentViewerPane
          target={target}
          className="h-full rounded-none border-0 border-l border-border"
          viewportClassName="p-4"
          headerActions={
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              aria-label="Cerrar vista previa"
              className="bg-white"
            >
              <X className="h-4 w-4" />
              Cerrar
            </Button>
          }
        />
      </div>
    </div>
  );
}
