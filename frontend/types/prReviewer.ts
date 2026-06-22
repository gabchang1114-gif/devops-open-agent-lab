export type PrReviewRisk = "low" | "medium" | "high";
export type PrReviewRecommendation = "approve" | "comment" | "request_changes";

export interface PrReviewFinding {
  severity: PrReviewRisk;
  category: string;
  file: string;
  line_reference: string;
  issue: string;
  why_it_matters: string;
  recommendation: string;
  example_fix: string;
}

export interface PrReviewAnalysis {
  summary: string;
  overall_risk: PrReviewRisk;
  should_block_merge: boolean;
  findings: PrReviewFinding[];
  positive_observations: string[];
  final_recommendation: PrReviewRecommendation;
}

export interface PrReviewHistoryItem {
  id: string;
  owner: string;
  repository: string;
  pull_request_number: number;
  pull_request_title?: string | null;
  overall_risk?: PrReviewRisk | null;
  findings_count: number;
  final_recommendation?: PrReviewRecommendation | null;
  status: string;
  created_at: string;
  commit_sha?: string | null;
}

export interface PrReviewHistoryResponse {
  reviews: PrReviewHistoryItem[];
}

export interface PrReviewDetail {
  id: string;
  owner: string;
  repository: string;
  pull_request_number: number;
  pull_request_title?: string | null;
  pull_request_author?: string | null;
  base_branch?: string | null;
  head_branch?: string | null;
  commit_sha?: string | null;
  overall_risk?: PrReviewRisk | null;
  findings_count: number;
  final_recommendation?: PrReviewRecommendation | null;
  status: string;
  current_step?: string | null;
  progress_percentage: number;
  review_markdown?: string | null;
  review?: PrReviewAnalysis | null;
  github_comment_url?: string | null;
  error?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface PrReviewStatus {
  review_id: string;
  status: string;
  current_step?: string | null;
  progress_percentage: number;
  error?: string | null;
}

export interface ManualReviewRequest {
  owner: string;
  repo: string;
  pull_request_number: number;
}

export interface ReviewStartResponse {
  review_id: string;
  status: string;
  message: string;
}
