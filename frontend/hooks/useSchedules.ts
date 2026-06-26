"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { scheduleApi } from "@/services/scheduleApi";
import type { InvestigationScheduleInput } from "@/types/schedule";

export function useSchedules() {
  const queryClient = useQueryClient();

  const schedulesQuery = useQuery({
    queryKey: ["kubernetes-schedules"],
    queryFn: () => scheduleApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (payload: InvestigationScheduleInput) => scheduleApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["kubernetes-schedules"] }),
  });

  const updateMutation = useMutation({
    mutationFn: ({
      scheduleId,
      payload,
    }: {
      scheduleId: string;
      payload: Partial<InvestigationScheduleInput>;
    }) => scheduleApi.update(scheduleId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["kubernetes-schedules"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (scheduleId: string) => scheduleApi.remove(scheduleId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["kubernetes-schedules"] }),
  });

  return {
    schedules: schedulesQuery.data ?? [],
    isLoading: schedulesQuery.isLoading,
    error: schedulesQuery.error,
    createSchedule: createMutation.mutateAsync,
    updateSchedule: updateMutation.mutateAsync,
    deleteSchedule: deleteMutation.mutateAsync,
    isSaving: createMutation.isPending || updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    saveError: createMutation.error ?? updateMutation.error,
    deleteError: deleteMutation.error,
  };
}
