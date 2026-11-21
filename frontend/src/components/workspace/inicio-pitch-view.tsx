"use client";

import {
  AlertTriangle,
  ArrowRight,
  Briefcase,
  CheckCircle2,
  Eye,
  FileSearch,
  GitCompareArrows,
  Layers,
  Quote,
  Scale,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const AGENTS = [
  {
    step: "01",
    name: "Clasificador Documental",
    role: "Identifica y clasifica cada archivo recibido",
    detail:
      "Reconoce automáticamente si cada documento corresponde a Escrituras, Predial, Alineamiento y Número Oficial o Uso de Suelo, y detecta faltantes desde el inicio.",
    icon: Layers,
  },
  {
    step: "02",
    name: "Extractor Especializado",
    role: "Extrae campos clave por tipo documental",
    detail:
      "Obtiene los datos estructurados requeridos para cada documento (titular, dirección, superficie, clave predial, número oficial, giro autorizado, vigencia y autoridad).",
    icon: FileSearch,
  },
  {
    step: "03",
    name: "Validador de Reglas",
    role: "Evalúa criterios normativos y completitud",
    detail:
      "Contrasta los datos extraídos contra las reglas y criterios proporcionados para detectar documentos incompletos, vencimientos, condicionantes o información faltante.",
    icon: ShieldCheck,
  },
  {
    step: "04",
    name: "Validador Cruzado",
    role: "Contrasta coherencia entre los documentos",
    detail:
      "Compara dirección, propietario, superficie, número oficial e identificación del predio entre todo el expediente para detectar inconsistencias o mezcla de inmuebles.",
    icon: GitCompareArrows,
  },
  {
    step: "05",
    name: "Verificador de Evidencia",
    role: "Ancla cada hallazgo al documento original",
    detail:
      "Anota cada observación y discrepancia con referencia verificable al archivo, página y fragmento exacto que la sustenta, eliminando conclusiones sin soporte.",
    icon: Quote,
  },
  {
    step: "06",
    name: "Dictaminador y Explicador Legal",
    role: "Emite recomendación inicial y justificación",
    detail:
      "Sintetiza hallazgos, riesgos y nivel de confianza en una recomendación clara (Cumple, Requiere revisión o No cumple) explicada para el equipo legal.",
    icon: Sparkles,
  },
] as const;

const CHALLENGE_CAPABILITIES = [
  {
    number: "01",
    requirement:
      "Identificar y clasificar automáticamente el tipo de documento recibido.",
    owner: "Agente 01 · Clasificador",
  },
  {
    number: "02",
    requirement:
      "Extraer la información relevante definida para cada tipo documental.",
    owner: "Agente 02 · Extractor",
  },
  {
    number: "03",
    requirement:
      "Validar la información contra los criterios y reglas proporcionados.",
    owner: "Agente 03 · Reglas",
  },
  {
    number: "04",
    requirement:
      "Detectar documentos incompletos, inconsistencias, riesgos o información faltante.",
    owner: "Agentes 03 y 04 · Riesgos",
  },
  {
    number: "05",
    requirement:
      "Realizar validaciones cruzadas entre documentos del mismo inmueble: dirección, propietario, superficie, identificación del predio y otros datos relevantes.",
    owner: "Agente 04 · Cruzado",
  },
  {
    number: "06",
    requirement:
      "Anotar los hallazgos indicando qué información o evidencia dentro del documento sustenta cada observación.",
    owner: "Agente 05 · Evidencia",
  },
  {
    number: "07",
    requirement:
      "Generar una recomendación inicial: Cumple, Requiere revisión o No cumple.",
    owner: "Agente 06 · Dictaminador",
  },
  {
    number: "08",
    requirement:
      "Explicar con claridad las razones de la recomendación para facilitar la revisión del equipo legal.",
    owner: "Agente 06 · Explicador",
  },
] as const;

const READING_LAYERS = [
  {
    level: "Nivel 1 · Decisión rápida",
    audience: "Gestor y Abogado",
    description:
      "Semáforo inicial (Cumple · Requiere revisión · No cumple), nivel de confianza del análisis, checklist documental y resumen ejecutivo en segundos.",
  },
  {
    level: "Nivel 2 · Contraste accionable",
    audience: "Validación operativa",
    description:
      "Requisitos cumplidos y no cumplidos junto con discrepancias cruzadas lado a lado: qué documentos difieren y qué valor reporta cada uno.",
  },
  {
    level: "Nivel 3 · Caja de cristal IA",
    audience: "Auditoría legal",
    description:
      "Sin ocultar cómo trabaja la IA: fragmento y página exacta que sustenta cada hallazgo, datos extraídos por campo y traza visible de los 6 agentes.",
  },
] as const;

export function InicioPitchView({
  onStartDemo,
}: {
  onStartDemo: () => void;
}) {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-primary/20 bg-secondary/45 px-5 py-4">
        <div className="space-y-1">
          <p className="text-sm font-semibold text-foreground">
            Listo para la demostración en vivo
          </p>
          <p className="text-xs text-muted-foreground">
            Pasa directo a cargar un expediente, revisar campos extraídos con
            visor PDF y auditar el flujo de 6 agentes.
          </p>
        </div>
        <Button type="button" onClick={onStartDemo}>
          Probar con un expediente
          <ArrowRight className="h-4 w-4" />
        </Button>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="border-border bg-white">
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Briefcase className="h-4 w-4 text-primary" />
                Para el Gestor Inmobiliario
              </CardTitle>
              <Badge variant="secondary" className="border-border text-primary">
                Simple y accionable
              </Badge>
            </div>
            <CardDescription>
              Velocidad para filtrar expedientes y corregir faltantes a tiempo.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed text-muted-foreground">
            Sube el expediente sin clasificar archivo por archivo y recibe de
            inmediato el semáforo inicial, qué documentos llegaron o faltan y
            qué observaciones concretas debe aclarar antes de escalar el caso.
          </CardContent>
        </Card>

        <Card className="border-border bg-white">
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Scale className="h-4 w-4 text-primary" />
                Para el Equipo Legal
              </CardTitle>
              <Badge variant="secondary" className="border-border text-primary">
                Auditable y trazable
              </Badge>
            </div>
            <CardDescription>
              Transparencia total de la IA sin sustituir el criterio jurídico.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed text-muted-foreground">
            Cada observación muestra las reglas aplicadas, las contradicciones
            cruzadas entre documentos, el nivel de confianza y la cita exacta
            del documento original para validar el dictamen sin leer todo desde
            cero.
          </CardContent>
        </Card>
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Arquitectura multiagente · LangChain
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-foreground">
              Cómo colaboran los 6 agentes especializados
            </h2>
          </div>
          <Badge variant="outline" className="border-border text-secondary-foreground">
            Flujo auditable de punta a punta
          </Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {AGENTS.map((agent) => {
            const Icon = agent.icon;
            return (
              <Card key={agent.step} className="border-border bg-white">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-primary">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="text-xs font-semibold tracking-wider text-primary">
                      AGENTE {agent.step}
                    </span>
                  </div>
                  <CardTitle className="pt-2 text-base">{agent.name}</CardTitle>
                  <CardDescription className="text-xs font-medium text-secondary-foreground">
                    {agent.role}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    {agent.detail}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <section>
        <Card className="border-border bg-white">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <CardTitle className="text-lg">
                  Cobertura de los 8 requisitos del reto
                </CardTitle>
                <CardDescription>
                  Cada capacidad exigida se asigna explícitamente a un agente
                  verificable del flujo.
                </CardDescription>
              </div>
              <Badge variant="default">8 / 8 cubiertos</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border rounded-xl border border-border">
              {CHALLENGE_CAPABILITIES.map((item) => (
                <li
                  key={item.number}
                  className="flex flex-col gap-2 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 text-xs font-semibold text-primary">
                      {item.number}
                    </span>
                    <p className="text-sm leading-snug text-foreground">
                      {item.requirement}
                    </p>
                  </div>
                  <Badge
                    variant="secondary"
                    className="w-fit shrink-0 border-border text-secondary-foreground"
                  >
                    {item.owner}
                  </Badge>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-primary" />
          <h2 className="text-lg font-semibold tracking-tight text-foreground">
            Brújula UX: simple al entrar, transparente al auditar
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {READING_LAYERS.map((layer) => (
            <Card key={layer.level} className="border-border bg-secondary/40">
              <CardHeader className="pb-2">
                <CardDescription className="text-xs font-semibold uppercase tracking-wide text-primary">
                  {layer.level}
                </CardDescription>
                <CardTitle className="text-base">{layer.audience}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {layer.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-white px-4 py-3 text-xs text-muted-foreground">
          <span className="font-semibold text-foreground">
            Salidas de dictamen posibles:
          </span>
          <Badge variant="success">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Cumple
          </Badge>
          <Badge variant="warning">
            <AlertTriangle className="h-3.5 w-3.5" />
            Requiere revisión
          </Badge>
          <Badge variant="destructive">No cumple</Badge>
        </div>
      </section>
    </div>
  );
}
