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
    tag: "Especialista 02",
    fields: [
      "Propietario o titular actual",
      "Dirección del inmueble",
      "Superficie del terreno",
      "Número de escritura e instrumento",
      "Notaría y notario",
      "Fecha de otorgamiento",
    ],
  },
  {
    name: "Predial",
    tag: "Especialista 03",
    fields: [
      "Propietario o contribuyente",
      "Dirección del predio",
      "Clave catastral o cuenta predial",
      "Periodo o ejercicio pagado",
      "Superficie de terreno, si aparece",
    ],
  },
  {
    name: "Alineamiento y Número Oficial",
    tag: "Especialista 04",
    fields: [
      "Dirección oficial del inmueble",
      "Número oficial asignado",
      "Alineamiento determinado",
      "Fecha de expedición y vigencia",
      "Autoridad emisora",
    ],
  },
  {
    name: "Uso de Suelo",
    tag: "Especialista 05",
    fields: [
      "Dirección del inmueble",
      "Uso de suelo o giro autorizado",
      "Restricciones o condicionantes",
      "Fecha de expedición y vigencia",
      "Autoridad emisora",
    ],
  },
] as const;

const CROSS_CHECKS = [
  "Dirección entre documentos.",
  "Número oficial.",
  "Propietario, en particular escritura contra predial.",
  "Superficie, con la tolerancia del YAML.",
  "Clave catastral o identificación del predio.",
  "Señales de que un documento pertenece a otro inmueble.",
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
            Recepción clasifica cada archivo por su contenido, no por el nombre.
            Los cuatro especialistas extraen los campos definidos en
            config/reglas.
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
                Campos del YAML de este especialista
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
            El Validador cruzado corre siempre, aunque falte un documento o un
            especialista falle. Cada discrepancia guarda el valor en cada
            documento y la evidencia. El Dictamen verifica después que la cita
            esté en el OCR.
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
