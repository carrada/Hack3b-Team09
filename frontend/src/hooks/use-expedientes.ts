"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  checkBackendHealth,
  createExpediente,
  getExpediente,
  listExpedientes,
  revalidarExpediente,
} from "@/lib/api";
import type {
  CrearExpedienteInput,
  RevalidarExpedientePayload,
} from "@/lib/contracts";

export const expedienteKeys = {
  all: ["expedientes"] as const,
  list: () => [...expedienteKeys.all, "list"] as const,
  detail: (id: string) => [...expedienteKeys.all, "detail", id] as const,
  health: ["backend", "health"] as const,
};

export function useBackendHealth() {
  return useQuery({
    queryKey: expedienteKeys.health,
    queryFn: ({ signal }) => checkBackendHealth(signal),
    retry: false,
    staleTime: 30_000,
  });
}

export function useExpedientes() {
  return useQuery({
    queryKey: expedienteKeys.list(),
    queryFn: ({ signal }) => listExpedientes(signal),
  });
}

export function useExpediente(expedienteId: string | null) {
  return useQuery({
    queryKey: expedienteId
      ? expedienteKeys.detail(expedienteId)
      : ["expedientes", "detail", "none"],
    queryFn: ({ signal }) => {
      if (!expedienteId) {
        throw new Error("expedienteId requerido");
      }
      return getExpediente(expedienteId, signal);
    },
    enabled: Boolean(expedienteId),
    refetchInterval: (query) => {
      const estado = query.state.data?.estado;
      if (estado === "pendiente" || estado === "procesando") {
        return 2_500;
      }
      return false;
    },
  });
}

export function useCreateExpediente() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CrearExpedienteInput) => createExpediente(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: expedienteKeys.list() });
    },
  });
}

export function useRevalidarExpediente() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      expedienteId,
      payload,
    }: {
      expedienteId: string;
      payload: RevalidarExpedientePayload;
    }) => revalidarExpediente(expedienteId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(expedienteKeys.detail(data.expedienteId), data);
      void queryClient.invalidateQueries({ queryKey: expedienteKeys.list() });
    },
  });
}
