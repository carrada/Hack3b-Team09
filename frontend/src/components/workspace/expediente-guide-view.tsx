"use client";

import { FileCheck2, GitCompareArrows, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const REQUIRED_DOCUMENTS = [
  {
    name: "Escrituras",
    tag: "Documento 01",
    fields: [
      "Identificación del propietario o titular",
      "Dirección e identificación del inmueble",
      "Superficie del terreno",
      "Datos relevantes del inmueble",
      "Información que lo relaciona con el resto del expediente",
    ],
  },
  {
    name: "Predial",
    tag: "Documento 02",
    fields: [
      "Propietario o contribuyente",
      "Dirección del inmueble",
      "Cuenta o clave predial",
      "Superficie registrada",
      "Información que lo relaciona con los demás documentos",
    ],
  },
  {
    name: "Alineamiento y Número Oficial",
    tag: "Documento 03",
    fields: [
      "Dirección oficial del inmueble",
      "Número oficial asignado",
      "Identificación del predio",
      "Alineamiento determinado por la autoridad",
      "Fecha de emisión, vigencia y autoridad emisora",
    ],
  },
  {
    name: "Uso de Suelo",
    tag: "Documento 04",
    fields: [
      "Dirección e identificación del inmueble",
      "Uso de suelo autorizado y compatibilidad comercial",
      "Restricciones o condicionantes",
      "Superficie aplicable",
      "Fecha de emisión, vigencia y autoridad emisora",
    ],
  },
] as const;

const CROSS_CHECKS = [
  "Diferencias en la dirección del inmueble entre documentos.",
  "Diferencias en el nombre del propietario o titular.",
  "Diferencias relevantes en superficies registradas.",
  "Diferencias en número oficial asignado.",
  "Datos de identificación del predio o clave predial que no coinciden.",
  "Indicios de documentos pertenecientes a inmuebles distintos.",
  "Documentos faltantes, incompletos o que requieran revisión adicional.",
] as const;

export function ExpedienteGuideView() {
  return (
    <div className="flex flex-col gap-6">
      <Card className="border-border bg-secondary/40">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2 text-base text-secondary-foreground">
              <FileCheck2 className="h-4 w-4 text-primary" />
              Checklist del expediente inmobiliario
            </CardTitle>
            <Badge variant="secondary" className="border-border text-primary">
              4 tipos documentales mínimos
            </Badge>
          </div>
          <CardDescription>
            El sistema clasifica los archivos automáticamente y verifica que se
            extraiga y contraste la información clave de cada documento.
          </CardDescription>
        </CardHeader>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {REQUIRED_DOCUMENTS.map((doc) => (
          <Card key={doc.name} className="border-border bg-white">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="text-base">{doc.name}</CardTitle>
                <Badge variant="outline" className="border-border text-primary">
                  {doc.tag}
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Información relevante que extrae el Agente 02
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5 text-sm text-muted-foreground">
                {doc.fields.map((field) => (
                  <li key={field} className="flex items-start gap-2">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                    <span>{field}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-border bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <GitCompareArrows className="h-4 w-4 text-primary" />
            Validaciones cruzadas entre documentos
          </CardTitle>
          <CardDescription>
            Además de revisar cada archivo por separado, el Agente 04 relaciona
            el expediente completo y el Agente 05 señala qué documentos
            discrepan, qué valor apareció en cada uno y dónde está la evidencia.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2.5 sm:grid-cols-2">
            {CROSS_CHECKS.map((check) => (
              <div
                key={check}
                className="flex items-start gap-2.5 rounded-lg border border-border bg-secondary/30 p-3 text-xs leading-relaxed text-foreground"
              >
                <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                <span>{check}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
