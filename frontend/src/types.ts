// Enums matching backend Pydantic StrEnums
export type Source = "email" | "call" | "slack" | "chat" | "other";
export type Priority = "low" | "medium" | "high";
export type Status = "new" | "in_progress" | "done";
export type Role = "admin" | "member";

// Auth
export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: Role;
}

export interface User {
  id: string;
  username: string;
  role: Role;
  created_at: string;
}

// Feedback
export interface Feedback {
  id: string;
  title: string;
  description: string;
  source: Source;
  priority: Priority;
  status: Status;
  created_by: string;
  idempotency_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeedbackListResponse {
  items: Feedback[];
  total: number;
  page: number;
  per_page: number;
}

export interface FeedbackCreate {
  title: string;
  description: string;
  source: Source;
  priority: Priority;
  status?: Status;
}

export interface FeedbackUpdate {
  title: string;
  description: string;
  source: Source;
  priority: Priority;
  status: Status;
}

// Dashboard
export interface DailyTrend {
  date: string;
  count: number;
}

export interface DashboardResponse {
  status_counts: Record<string, number>;
  priority_counts: Record<string, number>;
  daily_trend: DailyTrend[];
}

// Insights
export interface Insight {
  theme: string;
  confidence: number;
  justification: string;
}

export interface InsightsResponse {
  insights: Insight[];
  feedback_count?: number;
  model_used?: string;
  generated_at?: string;
  stale: boolean;
  message?: string;
}

// Common
export interface ErrorResponse {
  detail: string | object[];
  status_code: number;
  request_id: string;
}
