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
    name: "Recepción",
    role: "OCR, clasificación por contenido, agrupación y faltantes",
    detail:
      "Descarta no-documentos y duplicados, hace OCR, clasifica por contenido (palabras clave del YAML más el modelo) y extrae una huella para agrupar por inmueble. Detecta qué tipos faltan.",
    icon: Layers,
  },
  {
    step: "02",
    name: "Especialista Escrituras",
    role: "Extracción y reglas de la escritura pública",
    detail:
      "Extrae cada campo como valor, página y fragmento literal. Evalúa config/reglas/escrituras.yaml y devuelve Cumple, Requiere revisión o No cumple, con motivos.",
    icon: FileSearch,
  },
  {
    step: "03",
    name: "Especialista Predial",
    role: "Extracción y reglas de la boleta predial",
    detail:
      "Lee propietario, dirección, clave catastral y periodo pagado. Un predial a nombre de otra persona es discrepancia menor: Requiere revisión, no rechazo.",
    icon: ShieldCheck,
  },
  {
    step: "04",
    name: "Especialista Alineamiento y Número Oficial",
    role: "Extracción y reglas de la constancia",
    detail:
      "Extrae dirección oficial, número oficial, alineamiento, vigencia y autoridad. Las reglas salen de config/reglas/alineamiento.yaml.",
    icon: Quote,
  },
  {
    step: "05",
    name: "Especialista Uso de Suelo",
    role: "Extracción y reglas de la licencia o constancia",
    detail:
      "Extrae el uso autorizado y lo contrasta con el uso requerido (tienda o CEDIS). La incompatibilidad clara, con palabras del YAML, es el caso que puede producir No cumple.",
    icon: Scale,
  },
  {
    step: "06",
    name: "Validador cruzado",
    role: "Corre siempre, aunque falte un documento",
    detail:
      "Compara dirección, número oficial, propietario (escritura y predial), superficie, clave catastral y señales de otro inmueble. El modelo solo desempata direcciones ambiguas.",
    icon: GitCompareArrows,
  },
] as const;

const CHALLENGE_CAPABILITIES = [
  {
    number: "01",
    requirement:
      "Identificar y clasificar automáticamente el tipo de documento recibido.",
    owner: "Recepción",
  },
  {
    number: "02",
    requirement:
      "Extraer la información relevante definida para cada tipo documental.",
    owner: "Especialistas",
  },
  {
    number: "03",
    requirement:
      "Validar la información contra los criterios y reglas proporcionados.",
    owner: "Especialistas",
  },
  {
    number: "04",
    requirement:
      "Detectar documentos incompletos, inconsistencias, riesgos o información faltante.",
    owner: "Recepción y especialistas",
  },
  {
    number: "05",
    requirement:
      "Realizar validaciones cruzadas entre documentos del mismo inmueble: dirección, propietario, superficie, identificación del predio y otros datos relevantes.",
    owner: "Validador cruzado",
  },
  {
    number: "06",
    requirement:
      "Anotar los hallazgos indicando qué información o evidencia dentro del documento sustenta cada observación.",
    owner: "Dictamen",
  },
  {
    number: "07",
    requirement:
      "Generar una recomendación inicial: Cumple, Requiere revisión o No cumple.",
    owner: "Dictamen",
  },
  {
    number: "08",
    requirement:
      "Explicar con claridad las razones de la recomendación para facilitar la revisión del equipo legal.",
    owner: "Dictamen",
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
      "Sin ocultar cómo trabaja la IA: fragmento y página verificados contra el OCR, datos extraídos por campo y la bitácora real de los 6 agentes más el Dictamen.",
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

        <Card className="border-border bg-secondary/40">
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="h-4 w-4 text-primary" />
                Cierre · Dictamen
              </CardTitle>
              <Badge variant="outline" className="border-border text-primary">
                Cierre del grafo
              </Badge>
            </div>
            <CardDescription>
              La Recepción vuelve como validador final, después de los 6 agentes.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed text-muted-foreground">
            Verifica que cada fragmento citado exista en el texto OCR, calcula
            la confianza con señales medibles y aplica las reglas de dictamen.
            Emite Cumple, Requiere revisión o No cumple. Si no es Cumple, la
            respuesta marca revisión humana y lista los puntos a verificar. Un
            juicio del modelo nunca rechaza por sí solo.
          </CardContent>
        </Card>
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
                  Cada capacidad queda en el agente que realmente la ejecuta en
                  el grafo. La evidencia y la recomendación las cierra el
                  Dictamen.
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
