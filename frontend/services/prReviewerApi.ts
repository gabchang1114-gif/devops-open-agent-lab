import { apiClient } from "@/services/api";
import type {
  ManualReviewRequest,
  PrReviewDetail,
  PrReviewHistoryResponse,
  PrReviewStatus,
  ReviewStartResponse,
} from "@/types/prReviewer";

export const prReviewerApi = {
  async listHistory(limit = 50): Promise<PrReviewHistoryResponse> {
    const response = await apiClient.get<PrReviewHistoryResponse>(
      "/api/v1/pr-reviewer/history",
      { params: { limit } },
    );
    return response.data;
  },

  async getReview(reviewId: string): Promise<PrReviewDetail> {
    const response = await apiClient.get<PrReviewDetail>(
      `/api/v1/pr-reviewer/reviews/${reviewId}`,
    );
    return response.data;
  },

  async getReviewStatus(reviewId: string): Promise<PrReviewStatus> {
    const response = await apiClient.get<PrReviewStatus>(
      `/api/v1/pr-reviewer/reviews/${reviewId}/status`,
    );
    return response.data;
  },

  async startReview(request: ManualReviewRequest): Promise<ReviewStartResponse> {
    const response = await apiClient.post<ReviewStartResponse>(
      "/api/v1/pr-reviewer/review",
      request,
      { timeout: 30_000 },
    );
    return response.data;
  },
};
