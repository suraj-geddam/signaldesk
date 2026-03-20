import type {
  Feedback,
  FeedbackCreate,
  FeedbackUpdate,
  LoginResponse,
} from "./types";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function extractErrorMessage(data: unknown): string {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (typeof first === "object" && first !== null && "msg" in first) {
        return String((first as { msg: unknown }).msg);
      }
    }
  }
  return "An unexpected error occurred";
}

async function request<T>(
  method: string,
  path: string,
  options: {
    token?: string;
    body?: unknown;
    headers?: Record<string, string>;
  } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(extractErrorMessage(data));
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Auth
export async function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  return request<LoginResponse>("POST", "/auth/login", {
    body: { username, password },
  });
}

export async function getMe(
  token: string,
): Promise<{ id: string; username: string; role: string; created_at: string }> {
  return request("GET", "/auth/me", { token });
}

// Feedback mutations
export async function createFeedback(
  token: string,
  data: FeedbackCreate,
  idempotencyKey?: string,
): Promise<Feedback> {
  const headers: Record<string, string> = {};
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }
  return request<Feedback>("POST", "/feedback", {
    token,
    body: data,
    headers,
  });
}

export async function updateFeedback(
  token: string,
  id: string,
  data: FeedbackUpdate,
): Promise<Feedback> {
  return request<Feedback>("PUT", `/feedback/${id}`, { token, body: data });
}

export async function deleteFeedback(
  token: string,
  id: string,
): Promise<void> {
  return request<void>("DELETE", `/feedback/${id}`, { token });
}

// Insights
export async function refreshInsights(
  token: string,
): Promise<{ message: string }> {
  return request<{ message: string }>("POST", "/feedback/insights/refresh", {
    token,
  });
}
