export type ScheduleKind = "hourly" | "daily" | "weekly" | "custom";

export interface InvestigationSchedule {
  id: string;
  agent_type: string;
  name: string;
  cluster_id: string;
  namespace: string | null;
  query: string | null;
  include_ai: boolean;
  schedule_kind: ScheduleKind;
  hour: number;
  minute: number;
  day_of_week: number;
  cron_expression: string;
  timezone: string;
  enabled: boolean;
  last_run_at: string | null;
  last_investigation_id: string | null;
  last_status: string | null;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvestigationScheduleInput {
  name: string;
  cluster_id: string;
  namespace?: string | null;
  query?: string | null;
  include_ai: boolean;
  schedule_kind: ScheduleKind;
  hour: number;
  minute: number;
  day_of_week: number;
  cron_expression?: string | null;
  timezone: string;
  enabled: boolean;
}

export interface InvestigationScheduleListResponse {
  schedules: InvestigationSchedule[];
}

export const SCHEDULE_KIND_OPTIONS: Array<{
  value: ScheduleKind;
  label: string;
  description: string;
}> = [
  { value: "hourly", label: "Every hour", description: "Runs at the start of each hour" },
  { value: "daily", label: "Every day", description: "Runs once per day at a set time (UTC)" },
  { value: "weekly", label: "Every week", description: "Runs weekly on a chosen day (UTC)" },
  { value: "custom", label: "Custom cron", description: "5-field cron expression" },
];

export const DAY_OF_WEEK_OPTIONS = [
  { value: 0, label: "Sunday" },
  { value: 1, label: "Monday" },
  { value: 2, label: "Tuesday" },
  { value: 3, label: "Wednesday" },
  { value: 4, label: "Thursday" },
  { value: 5, label: "Friday" },
  { value: 6, label: "Saturday" },
];
