import { z } from "zod";

const BooleanFlagSchema = z
  .enum(["true", "false", "1", "0"])
  .optional()
  .transform((value) => value === "true" || value === "1");

const PublicEnvSchema = z.object({
  apiBaseUrl: z
    .string()
    .trim()
    .min(1)
    .default("http://localhost:8000")
    .transform((url) => url.replace(/\/+$/, "")),
  useMocks: BooleanFlagSchema,
  appName: z
    .string()
    .trim()
    .min(1)
    .default("Expedientes 3B · Revisión Inteligente"),
});

export type FrontendConfig = z.infer<typeof PublicEnvSchema>;

function parsePublicEnv(): FrontendConfig {
  const rawUseMocks = process.env.NEXT_PUBLIC_USE_MOCKS;

  const parsed = PublicEnvSchema.safeParse({
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || undefined,
    // Default to mocks when no explicit flag and no explicit backend URL are provided
    useMocks:
      rawUseMocks ??
      (process.env.NEXT_PUBLIC_API_BASE_URL ? "false" : "true"),
    appName: process.env.NEXT_PUBLIC_APP_NAME || undefined,
  });

  if (!parsed.success) {
    return {
      apiBaseUrl: "http://localhost:8000",
      useMocks: true,
      appName: "Expedientes 3B · Revisión Inteligente",
    };
  }

  return parsed.data;
}

export const env: FrontendConfig = parsePublicEnv();

const LOOPBACK = new Set(["localhost", "127.0.0.1", "::1", "[::1]"]);

function hostDe(url: string): string | null {
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}

/**
 * En el navegador, si la página no está en esta máquina —o el API configurado
 * es loopback— la carga usa el mismo origen. Next reenvía `/api/v1` al proceso
 * en 127.0.0.1:8000, así un solo puerto sirve la app y el análisis.
 * En el servidor se conserva la URL configurada.
 */
export function resolveApiBaseUrl(): string {
  const configured = env.apiBaseUrl;
  if (typeof window === "undefined") return configured;

  const paginaAqui = LOOPBACK.has(window.location.hostname);
  const apiHost = hostDe(configured);
  const apiAqui = apiHost !== null && LOOPBACK.has(apiHost);
  if (!paginaAqui || apiAqui) return "";
  return configured;
}
