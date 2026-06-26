import { apiClient } from "@/services/api";
import type {
  InvestigationSchedule,
  InvestigationScheduleInput,
  InvestigationScheduleListResponse,
} from "@/types/schedule";

export const scheduleApi = {
  async list(): Promise<InvestigationSchedule[]> {
    const response = await apiClient.get<InvestigationScheduleListResponse>(
      "/api/v1/kubernetes/schedules",
    );
    return response.data.schedules;
  },

  async create(payload: InvestigationScheduleInput): Promise<InvestigationSchedule> {
    const response = await apiClient.post<InvestigationSchedule>(
      "/api/v1/kubernetes/schedules",
      payload,
    );
    return response.data;
  },

  async update(
    scheduleId: string,
    payload: Partial<InvestigationScheduleInput>,
  ): Promise<InvestigationSchedule> {
    const response = await apiClient.put<InvestigationSchedule>(
      `/api/v1/kubernetes/schedules/${scheduleId}`,
      payload,
    );
    return response.data;
  },

  async remove(scheduleId: string): Promise<void> {
    await apiClient.delete(`/api/v1/kubernetes/schedules/${scheduleId}`);
  },
};
