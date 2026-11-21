"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DocumentoLadoALado } from "@/components/workspace/documento-lado-a-lado";
import {
  ETIQUETA_RECOMENDACION,
  type AnalisisEstado,
  type RecomendacionBackend,
} from "@/lib/contracts";
import { etiquetaCampo } from "@/lib/workspace/campos-documento";

type Seccion = "resumen" | "documentos" | "cruces" | "bitacora";

const SECCIONES: { id: Seccion; label: string }[] = [
  { id: "resumen", label: "Resumen" },
  { id: "documentos", label: "Documentos" },
  { id: "cruces", label: "Cruces" },
  { id: "bitacora", label: "Bitácora" },
];

function variante(recomendacion: RecomendacionBackend) {
  if (recomendacion === "cumple") return "success" as const;
  if (recomendacion === "no_cumple") return "destructive" as const;
  return "warning" as const;
}

export function ResultadoView({
  analisis,
  files,
  manuales,
  isRunning,
  error,
  elapsedSec,
}: {
  analisis: AnalisisEstado | null;
  files: File[];
  manuales: Record<string, string>;
  isRunning: boolean;
  error: string | null;
  elapsedSec: number | null;
}) {
  const [seccion, setSeccion] = useState<Seccion>("resumen");

  if (!analisis) {
    return (
      <Card className="border-border bg-white">
        <CardHeader>
          <CardTitle className="text-base">Aún no hay dictamen</CardTitle>
          <CardDescription>
            En Carga sube los PDF y detecta los campos. El dictamen aparece aquí
            cuando el grafo termina.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {error}
            </p>
          )}
          {isRunning && (
            <p className="text-sm text-muted-foreground">El grafo sigue en curso.</p>
          )}
        </CardContent>
      </Card>
    );
  }

  const { dictamen, bitacora, resultados_verificados, cruces, discrepancias } = analisis;
  const capturas = Object.entries(manuales);

  return (
    <div className="flex flex-col gap-5">
      <Card className="border-border bg-white">
        <CardContent className="flex flex-col gap-4 pt-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                Dictamen
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <Badge variant={variante(dictamen.recomendacion)} className="text-sm">
                  {ETIQUETA_RECOMENDACION[dictamen.recomendacion]}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Confianza {dictamen.confianza}/100 · {dictamen.uso_requerido}
                  {elapsedSec !== null ? ` · ${elapsedSec.toFixed(1)} s` : ""}
                </span>
              </div>
            </div>
            {dictamen.requiere_humano && (
              <Badge variant="warning">Revisión humana</Badge>
            )}
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${Math.max(0, Math.min(100, dictamen.confianza))}%` }}
            />
          </div>
          {dictamen.resumen && (
            <p className="text-sm leading-relaxed text-foreground">{dictamen.resumen}</p>
          )}
          <div className="grid gap-2 sm:grid-cols-3">
            <Dato titulo="Recibidos" valor={String(dictamen.documentos_recibidos.length)} />
            <Dato titulo="Faltantes" valor={String(dictamen.documentos_faltantes.length)} />
            <Dato
              titulo="Citas verificadas"
              valor={`${dictamen.citas_verificadas ?? 0}/${dictamen.citas_total ?? 0}`}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2">
        {SECCIONES.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setSeccion(item.id)}
            className={`rounded-full border px-3 py-1 text-sm font-medium ${
              seccion === item.id
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-white text-foreground"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {seccion === "resumen" && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Lista titulo="Por qué" items={dictamen.razones} vacio="Sin razones." />
          <div className="flex flex-col gap-4">
            <Lista titulo="Faltantes" items={dictamen.documentos_faltantes} vacio="Ninguno." />
            <Lista titulo="Descartados" items={dictamen.documentos_descartados} vacio="Ninguno." />
            <Lista
              titulo="Puntos a verificar"
              items={dictamen.puntos_a_verificar}
              vacio="Ninguno."
            />
          </div>
          {capturas.length > 0 && (
            <Card className="border-border bg-white lg:col-span-2">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Capturas manuales</CardTitle>
                <CardDescription>
                  Las escribió el usuario en Carga. El grafo no las revalidó.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1 text-sm">
                  {capturas.map(([clave, valor]) => (
                    <li key={clave}>
                      <span className="font-medium">{etiquetaDeClave(clave, resultados_verificados)}</span>
                      {": "}
                      {valor}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {seccion === "documentos" && (
        <DocumentoLadoALado
          files={files}
          resultados={resultados_verificados}
          manuales={manuales}
          editable={false}
        />
      )}

      {seccion === "cruces" && (
        <div className="flex flex-col gap-4">
          {discrepancias.length > 0 && (
            <Lista
              titulo="Inconsistencias"
              items={discrepancias.map(
                (item) => `${item.atributo} (${item.severidad}): ${item.explicacion}`,
              )}
              vacio="Ninguna."
            />
          )}
          <Card className="border-border bg-white">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Comparaciones del validador cruzado</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {cruces.length === 0 && (
                <p className="text-sm text-muted-foreground">Sin cruces.</p>
              )}
              {cruces.map((cruce) => (
                <div
                  key={`${cruce.atributo}-${cruce.score}-${cruce.resultado}`}
                  className="rounded-lg border border-border px-3 py-2 text-sm"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{cruce.atributo}</span>
                    <Badge variant={cruce.resultado === "coincide" ? "success" : "warning"}>
                      {cruce.resultado} · {cruce.score.toFixed(0)}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {Object.entries(cruce.valores)
                      .map(([id, valor]) => `${id}: ${valor}`)
                      .join(" · ")}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {seccion === "bitacora" && (
        <Card className="border-border bg-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Bitácora de los agentes</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-1 font-mono text-xs leading-relaxed">
              {bitacora.map((linea, index) => (
                <li key={`${index}-${linea}`}>{linea}</li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Dato({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div className="rounded-lg border border-border bg-secondary/30 px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{titulo}</p>
      <p className="text-sm font-semibold text-foreground">{valor}</p>
    </div>
  );
}

function Lista({
  titulo,
  items,
  vacio,
}: {
  titulo: string;
  items: string[];
  vacio: string;
}) {
  return (
    <Card className="border-border bg-white">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{titulo}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{vacio}</p>
        ) : (
          <ul className="space-y-1.5 text-sm leading-snug">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function etiquetaDeClave(
  clave: string,
  resultados: AnalisisEstado["resultados_verificados"],
): string {
  const separador = clave.indexOf("::");
  const documentoId = separador >= 0 ? clave.slice(0, separador) : clave;
  const nombre = separador >= 0 ? clave.slice(separador + 2) : clave;
  const doc = resultados.find((item) => item.documento_id === documentoId);
  const archivo = doc?.nombre_archivo ?? documentoId;
  return `${archivo} · ${etiquetaCampo(nombre)}`;
}
