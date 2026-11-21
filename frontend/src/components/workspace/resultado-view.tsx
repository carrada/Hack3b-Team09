"use client";

import { FileSearch } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ETIQUETA_RECOMENDACION,
  NOMBRES_TIPO_BACKEND,
  type AnalisisEstado,
  type EvidenciaBackend,
  type RecomendacionBackend,
} from "@/lib/contracts";

function variante(recomendacion: RecomendacionBackend) {
  if (recomendacion === "cumple") return "success" as const;
  if (recomendacion === "no_cumple") return "destructive" as const;
  return "warning" as const;
}

function cita(ev?: EvidenciaBackend | null): string {
  if (!ev?.fragmento) return "—";
  const marca = ev.verificada ? "verificada" : "no verificada";
  return `${ev.documento_id} p.${ev.pagina}: «${ev.fragmento}» (${marca})`;
}

export function ResultadoView({
  analisis,
  isRunning,
  error,
  elapsedSec,
  onPreviewDoc,
}: {
  analisis: AnalisisEstado | null;
  isRunning: boolean;
  error: string | null;
  elapsedSec: number | null;
  onPreviewDoc: (nombreArchivo: string, pagina?: number) => void;
}) {
  if (!analisis) {
    return (
      <Card className="border-border bg-white">
        <CardHeader>
          <CardTitle className="text-base">Aún no hay dictamen</CardTitle>
          <CardDescription>
            Carga los archivos, elige tienda o CEDIS y espera a que el grafo
            termine. Esta pantalla no simula agentes.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
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

  const { dictamen, bitacora, resultados_verificados, cruces, discrepancias } =
    analisis;

  return (
    <div className="flex flex-col gap-6">
      <Card className="border-border bg-white">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-base">Dictamen del grafo</CardTitle>
            <Badge variant={variante(dictamen.recomendacion)}>
              {ETIQUETA_RECOMENDACION[dictamen.recomendacion]}
            </Badge>
          </div>
          <CardDescription>
            Confianza {dictamen.confianza}/100 · uso {dictamen.uso_requerido} ·
            citas {dictamen.citas_verificadas ?? 0}/{dictamen.citas_total ?? 0}
            {dictamen.requiere_humano ? " · revisión humana" : ""}
            {elapsedSec !== null ? ` · ${elapsedSec.toFixed(1)} s` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-foreground">
          {dictamen.resumen && <p>{dictamen.resumen}</p>}
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-primary">
              Razones
            </p>
            <ul className="space-y-1 text-sm">
              {dictamen.razones.map((razon) => (
                <li key={razon}>{razon}</li>
              ))}
            </ul>
          </div>
          {dictamen.requiere_humano && dictamen.puntos_a_verificar.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-primary">
                Puntos a verificar
              </p>
              <ul className="list-disc space-y-1 pl-5">
                {dictamen.puntos_a_verificar.map((punto) => (
                  <li key={punto}>{punto}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Lista titulo="Recibidos" items={dictamen.documentos_recibidos} vacio="Ninguno" />
        <Lista titulo="Faltantes" items={dictamen.documentos_faltantes} vacio="Ninguno" />
        <Lista
          titulo="Descartados"
          items={dictamen.documentos_descartados}
          vacio="Ninguno"
        />
      </div>

      {resultados_verificados.map((resultado) => (
        <Card key={resultado.documento_id} className="border-border bg-white">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="text-base">
                {NOMBRES_TIPO_BACKEND[resultado.tipo]} — {resultado.nombre_archivo}
              </CardTitle>
              <Badge variant={variante(resultado.estado)}>
                {ETIQUETA_RECOMENDACION[resultado.estado]}
              </Badge>
            </div>
            <CardDescription>
              {resultado.agente}
              {resultado.calidad_ocr !== undefined
                ? ` · OCR ${(resultado.calidad_ocr * 100).toFixed(0)}%`
                : ""}
              {resultado.obligatorios_total !== undefined
                ? ` · obligatorios ${resultado.obligatorios_encontrados ?? 0}/${resultado.obligatorios_total}`
                : ""}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="py-1 pr-3 font-medium">Campo</th>
                    <th className="py-1 pr-3 font-medium">Valor</th>
                    <th className="py-1 font-medium">Evidencia</th>
                  </tr>
                </thead>
                <tbody>
                  {resultado.campos
                    .filter((campo) => campo.valor)
                    .map((campo) => (
                      <tr key={campo.nombre} className="border-t border-border align-top">
                        <td className="py-2 pr-3">{campo.nombre}</td>
                        <td className="py-2 pr-3">{campo.valor}</td>
                        <td className="py-2">
                          <button
                            type="button"
                            className="text-left text-primary underline-offset-2 hover:underline"
                            onClick={() =>
                              onPreviewDoc(
                                resultado.nombre_archivo,
                                campo.evidencia?.pagina,
                              )
                            }
                          >
                            {cita(campo.evidencia)}
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            <ul className="space-y-2 text-sm">
              {resultado.hallazgos.map((hallazgo) => (
                <li key={`${hallazgo.regla_id}-${hallazgo.descripcion}`}>
                  <span className="font-medium">{hallazgo.regla_id}</span>{" "}
                  <span className="text-muted-foreground">({hallazgo.severidad})</span>{" "}
                  {hallazgo.descripcion}
                  {hallazgo.evidencias.length > 0 && (
                    <ul className="mt-1 space-y-1 pl-4 text-xs text-muted-foreground">
                      {hallazgo.evidencias.map((ev) => (
                        <li key={`${ev.documento_id}-${ev.pagina}-${ev.fragmento}`}>
                          {cita(ev)}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
            {resultado.error && (
              <p className="text-sm text-red-800">{resultado.error}</p>
            )}
          </CardContent>
        </Card>
      ))}

      <Card className="border-border bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileSearch className="h-4 w-4 text-primary" />
            Validaciones cruzadas
          </CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {cruces.length === 0 ? (
            <p className="text-sm text-muted-foreground">Sin cruces.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="py-1 pr-3 font-medium">Atributo</th>
                  <th className="py-1 pr-3 font-medium">Valores</th>
                  <th className="py-1 pr-3 font-medium">Score</th>
                  <th className="py-1 font-medium">Resultado</th>
                </tr>
              </thead>
              <tbody>
                {cruces.map((cruce) => (
                  <tr
                    key={`${cruce.atributo}-${cruce.score}-${Object.values(cruce.valores).join("|")}`}
                    className="border-t border-border align-top"
                  >
                    <td className="py-2 pr-3">{cruce.atributo}</td>
                    <td className="py-2 pr-3">
                      {Object.entries(cruce.valores).map(([id, valor]) => (
                        <div key={id}>
                          {id}: {valor}
                        </div>
                      ))}
                    </td>
                    <td className="py-2 pr-3">{cruce.score.toFixed(0)}</td>
                    <td className="py-2">
                      {cruce.resultado} · {cruce.metodo}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {discrepancias.length > 0 && (
        <Card className="border-border bg-white">
          <CardHeader>
            <CardTitle className="text-base">Inconsistencias</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {discrepancias.map((item) => (
              <div key={`${item.atributo}-${item.explicacion}`}>
                <p>
                  <span className="font-medium">{item.atributo}</span>{" "}
                  <span className="text-muted-foreground">({item.severidad})</span>{" "}
                  {item.explicacion}
                </p>
                <ul className="mt-1 text-xs text-muted-foreground">
                  {Object.entries(item.valores).map(([id, valor]) => (
                    <li key={id}>
                      {id}: {valor}
                    </li>
                  ))}
                  {item.evidencias.map((ev) => (
                    <li key={`${ev.pagina}-${ev.fragmento}`}>{cita(ev)}</li>
                  ))}
                </ul>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Lista titulo="Requisitos cumplidos" items={dictamen.requisitos_cumplidos} vacio="Ninguno" />
        <Lista
          titulo="Requisitos no cumplidos"
          items={dictamen.requisitos_no_cumplidos}
          vacio="Ninguno"
        />
      </div>

      {Object.keys(dictamen.senales_confianza).length > 0 && (
        <Card className="border-border bg-white">
          <CardHeader>
            <CardTitle className="text-base">Señales de confianza</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2 text-sm">
            {Object.entries(dictamen.senales_confianza).map(([clave, valor]) => (
              <div key={clave} className="flex justify-between gap-3 border-b border-border py-1">
                <span>{clave.replaceAll("_", " ")}</span>
                <span>{Math.round(valor * 100)}%</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card className="border-border bg-white">
        <CardHeader>
          <CardTitle className="text-base">Bitácora</CardTitle>
          <CardDescription>
            Líneas que escribieron Recepción, los especialistas, el Validador
            cruzado y el Dictamen.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="space-y-1 font-mono text-xs leading-relaxed text-foreground">
            {bitacora.map((linea, index) => (
              <li key={`${index}-${linea}`}>{linea}</li>
            ))}
          </ol>
        </CardContent>
      </Card>
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
          <ul className="space-y-1 text-sm">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
