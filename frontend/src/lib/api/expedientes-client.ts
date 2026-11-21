import { env } from "@/lib/config/env";
import {
  AnalisisEstado,
  AnalisisEstadoSchema,
  CrearExpedienteInput,
  CrearExpedienteResponse,
  CrearExpedienteResponseSchema,
  ExpedienteAnalisis,
  ExpedienteAnalisisSchema,
  ExpedienteResumen,
  HealthResponse,
  HealthResponseSchema,
  ListaExpedientesResponseSchema,
  RevalidarExpedientePayload,
  UsoRequerido,
} from "@/lib/contracts";
import {
  mockCreateExpediente,
  mockGetExpediente,
  mockListExpedientes,
} from "@/lib/mocks/expedientes-mock";
import { ApiClientError, apiRequest } from "./http-client";

export const API_ENDPOINTS = {
  health: "/api/v1/health",
  analisis: "/api/v1/analisis",
  expedientes: "/api/v1/expedientes",
  expedienteById: (id: string) => `/api/v1/expedientes/${encodeURIComponent(id)}`,
  revalidarExpediente: (id: string) =>
    `/api/v1/expedientes/${encodeURIComponent(id)}/revalidar`,
} as const;

export async function checkBackendHealth(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  if (env.useMocks) {
    return { status: "ok", version: "mock-local" };
  }

  return apiRequest(API_ENDPOINTS.health, {
    method: "GET",
    schema: HealthResponseSchema,
    signal,
    timeoutMs: 8_000,
  });
}

export async function listExpedientes(
  signal?: AbortSignal,
): Promise<ExpedienteResumen[]> {
  if (env.useMocks) {
    return mockListExpedientes();
  }

  const data = await apiRequest(API_ENDPOINTS.expedientes, {
    method: "GET",
    schema: ListaExpedientesResponseSchema,
    signal,
  });

  return data.items;
}

export async function getExpediente(
  expedienteId: string,
  signal?: AbortSignal,
): Promise<ExpedienteAnalisis> {
  if (env.useMocks) {
    const mockItem = await mockGetExpediente(expedienteId);
    if (!mockItem) {
      throw new ApiClientError(`Expediente ${expedienteId} no encontrado.`, {
        status: 404,
        code: "NOT_FOUND",
      });
    }
    return mockItem;
  }

  return apiRequest(API_ENDPOINTS.expedienteById(expedienteId), {
    method: "GET",
    schema: ExpedienteAnalisisSchema,
    signal,
  });
}

export async function createExpediente(
  input: CrearExpedienteInput,
  signal?: AbortSignal,
): Promise<CrearExpedienteResponse> {
  if (env.useMocks) {
    return mockCreateExpediente(input);
  }

  const formData = new FormData();
  formData.append("nombre_expediente", input.nombreExpediente);
  for (const file of input.archivos) {
    formData.append("files", file);
  }

  return apiRequest(API_ENDPOINTS.expedientes, {
    method: "POST",
    body: formData,
    schema: CrearExpedienteResponseSchema,
    signal,
    timeoutMs: 60_000,
  });
}

export async function analizarExpediente(
  input: { uso: UsoRequerido; archivos: File[] },
  signal?: AbortSignal,
): Promise<AnalisisEstado> {
  if (env.useMocks) {
    throw new ApiClientError(
      "NEXT_PUBLIC_USE_MOCKS=true: el mock no inventa un dictamen. Pon la variable en false y arranca el backend en el puerto 8000.",
      { status: 0, code: "MOCKS_ENABLED" },
    );
  }

  const formData = new FormData();
  formData.append("uso", input.uso);
  for (const file of input.archivos) {
    formData.append("files", file);
  }

  return apiRequest(API_ENDPOINTS.analisis, {
    method: "POST",
    body: formData,
    schema: AnalisisEstadoSchema,
    signal,
    timeoutMs: 600_000,
  });
}

export async function revalidarExpediente(
  expedienteId: string,
  payload: RevalidarExpedientePayload,
  signal?: AbortSignal,
): Promise<ExpedienteAnalisis> {
  if (env.useMocks) {
    const existing = await mockGetExpediente(expedienteId);
    if (!existing) {
      throw new ApiClientError(`Expediente ${expedienteId} no encontrado.`, {
        status: 404,
        code: "NOT_FOUND",
      });
    }
    return {
      ...existing,
      actualizadoEn: new Date().toISOString(),
    };
  }

  return apiRequest(API_ENDPOINTS.revalidarExpediente(expedienteId), {
    method: "PATCH",
    body: payload,
    schema: ExpedienteAnalisisSchema,
    signal,
    timeoutMs: 60_000,
  });
}
