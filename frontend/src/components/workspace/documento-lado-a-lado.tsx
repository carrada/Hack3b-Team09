"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { DocumentViewerPane } from "@/components/workspace/document-viewer-pane";
import {
  ETIQUETA_RECOMENDACION,
  NOMBRES_TIPO_BACKEND,
  type ResultadoDocumentoBackend,
} from "@/lib/contracts";
import {
  archivoDe,
  claveManual,
  etiquetaCampo,
  tipoVista,
} from "@/lib/workspace/campos-documento";

export function DocumentoLadoALado({
  files,
  resultados,
  manuales,
  editable,
  onManualChange,
}: {
  files: File[];
  resultados: ResultadoDocumentoBackend[];
  manuales: Record<string, string>;
  editable: boolean;
  onManualChange?: (documentoId: string, nombre: string, valor: string) => void;
}) {
  const [seleccion, setSeleccion] = useState(resultados[0]?.documento_id ?? "");
  const [pagina, setPagina] = useState<number | undefined>(undefined);
  const [corrigiendo, setCorrigiendo] = useState<string | null>(null);

  const activo = useMemo(
    () =>
      resultados.find((item) => item.documento_id === seleccion) ??
      resultados[0],
    [resultados, seleccion],
  );

  if (!activo) {
    return (
      <p className="text-sm text-muted-foreground">
        El grafo no devolvió documentos para revisar.
      </p>
    );
  }

  const archivo = archivoDe(files, activo.nombre_archivo);
  const campos = [...activo.campos].sort((a, b) => {
    const aVacio = a.valor ? 1 : 0;
    const bVacio = b.valor ? 1 : 0;
    return aVacio - bVacio;
  });

  return (
    <div className="grid items-start gap-4 lg:grid-cols-2">
      <DocumentViewerPane
        className="lg:sticky lg:top-4"
        viewportClassName="min-h-[68vh]"
        target={{
          documentoId: activo.documento_id,
          nombreArchivo: activo.nombre_archivo,
          tipoDocumento: tipoVista(activo.tipo),
          etiquetaTipo: NOMBRES_TIPO_BACKEND[activo.tipo],
          file: archivo,
          page: pagina,
        }}
      />

      <div className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-wrap gap-2">
          {resultados.map((item) => {
            const activoItem = item.documento_id === activo.documento_id;
            return (
              <button
                key={item.documento_id}
                type="button"
                onClick={() => {
                  setSeleccion(item.documento_id);
                  setPagina(undefined);
                  setCorrigiendo(null);
                }}
                className={`rounded-full border px-3 py-1 text-xs font-medium ${
                  activoItem
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-white text-foreground"
                }`}
              >
                {NOMBRES_TIPO_BACKEND[item.tipo]}
              </button>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-foreground">
              {activo.nombre_archivo}
            </p>
            <p className="text-xs text-muted-foreground">{activo.agente}</p>
          </div>
          <Badge variant={activo.estado === "cumple" ? "success" : activo.estado === "no_cumple" ? "destructive" : "warning"}>
            {ETIQUETA_RECOMENDACION[activo.estado]}
          </Badge>
        </div>

        <ul className="flex flex-col gap-2">
          {campos.map((campo) => {
            const clave = claveManual(activo.documento_id, campo.nombre);
            const manual = manuales[clave] ?? "";
            const falta = !campo.valor;
            const mostrarInput = editable && (falta || corrigiendo === clave || manual.length > 0);
            return (
              <li
                key={campo.nombre}
                className="rounded-xl border border-border bg-white px-3 py-2.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium text-foreground">
                    {etiquetaCampo(campo.nombre)}
                  </p>
                  <Badge
                    variant={falta && !manual ? "warning" : manual ? "outline" : "success"}
                    className="shrink-0"
                  >
                    {manual ? "Captura manual" : falta ? "Falta" : "Detectado"}
                  </Badge>
                </div>
                {campo.valor && (
                  <p className="mt-1 text-sm text-foreground">{campo.valor}</p>
                )}
                {campo.evidencia?.fragmento && (
                  <button
                    type="button"
                    className="mt-1 text-left text-xs text-primary underline-offset-2 hover:underline"
                    onClick={() => setPagina(campo.evidencia?.pagina)}
                  >
                    Página {campo.evidencia.pagina}
                    {campo.evidencia.verificada ? " · cita verificada" : " · cita no verificada"}
                  </button>
                )}
                {mostrarInput && (
                  <input
                    value={manual}
                    onChange={(event) =>
                      onManualChange?.(activo.documento_id, campo.nombre, event.target.value)
                    }
                    placeholder={
                      falta
                        ? "No aparece en el documento. Escríbelo aquí."
                        : "Corrección para el equipo legal"
                    }
                    className="mt-2 h-9 w-full rounded-lg border border-border bg-white px-3 text-sm"
                  />
                )}
                {editable && campo.valor && !mostrarInput && (
                  <button
                    type="button"
                    className="mt-1 text-xs font-medium text-primary"
                    onClick={() => setCorrigiendo(clave)}
                  >
                    Corregir
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
