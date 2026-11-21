import { z } from "zod";
import { env } from "@/lib/config/env";

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(
    message: string,
    options: { status: number; code?: string; details?: unknown },
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = options.status;
    this.code = options.code ?? "API_ERROR";
    this.details = options.details;
  }
}

export interface RequestOptions<TSchema extends z.ZodType> {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown | FormData;
  headers?: HeadersInit;
  signal?: AbortSignal;
  timeoutMs?: number;
  schema: TSchema;
}

const DEFAULT_TIMEOUT_MS = 30_000;

function mensajeDetalle(payload: unknown): string | null {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) {
    return null;
  }
  const detail = payload.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const partes = detail.map((item) => {
      if (typeof item === "string") return item;
      if (typeof item === "object" && item !== null && "msg" in item) {
        return String(item.msg);
      }
      return "";
    });
    const texto = partes.filter(Boolean).join(" ");
    return texto || null;
  }
  return null;
}

export async function apiRequest<TSchema extends z.ZodType>(
  path: string,
  options: RequestOptions<TSchema>,
): Promise<z.infer<TSchema>> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${env.apiBaseUrl}${normalizedPath}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  );

  const onExternalAbort = () => controller.abort();
  options.signal?.addEventListener("abort", onExternalAbort, { once: true });

  const isFormData =
    typeof FormData !== "undefined" && options.body instanceof FormData;

  const headers = new Headers(options.headers);
  if (!isFormData && options.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  try {
    const response = await fetch(url, {
      method: options.method ?? "GET",
      headers,
      body:
        options.body === undefined
          ? undefined
          : isFormData
            ? (options.body as FormData)
            : JSON.stringify(options.body),
      signal: controller.signal,
    });

    const contentType = response.headers.get("content-type") ?? "";
    const payload = contentType.includes("application/json")
      ? await response.json().catch(() => null)
      : await response.text().catch(() => null);

    if (!response.ok) {
      const errorMessage =
        mensajeDetalle(payload) ??
        `Error HTTP ${response.status} al consultar ${normalizedPath}`;

      throw new ApiClientError(errorMessage, {
        status: response.status,
        code: "HTTP_ERROR",
        details: payload,
      });
    }

    const parsed = options.schema.safeParse(payload);
    if (!parsed.success) {
      throw new ApiClientError(
        `La respuesta de ${normalizedPath} no coincide con el contrato esperado.`,
        {
          status: response.status,
          code: "CONTRACT_MISMATCH",
          details: parsed.error.issues,
        },
      );
    }

    return parsed.data;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError(
        "Tiempo de espera agotado al comunicarse con el backend.",
        {
          status: 408,
          code: "TIMEOUT",
        },
      );
    }

    throw new ApiClientError(
      "No fue posible conectar con el backend configurado.",
      {
        status: 0,
        code: "NETWORK_ERROR",
        details: error,
      },
    );
  } finally {
    clearTimeout(timeoutId);
    options.signal?.removeEventListener("abort", onExternalAbort);
  }
}
