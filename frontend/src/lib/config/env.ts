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
