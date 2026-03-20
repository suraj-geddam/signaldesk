import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { AuthContext } from "../context/AuthContext";
import { InsightsPage } from "./InsightsPage";
import type { InsightsResponse, User } from "../types";

const adminUser: User = {
  id: "u1",
  username: "admin",
  role: "admin",
  created_at: "2024-01-01T00:00:00Z",
};

const mockInsights: InsightsResponse = {
  insights: [
    {
      theme: "SOC2 export requests",
      confidence: 0.85,
      justification: "12 mentions across email and call sources.",
    },
  ],
  feedback_count: 42,
  model_used: "gpt-4o-mini",
  generated_at: "2024-06-15T10:00:00Z",
  stale: false,
};

const staleInsights: InsightsResponse = {
  ...mockInsights,
  stale: true,
};

const emptyInsights: InsightsResponse = {
  insights: [],
  stale: false,
  message: "No insights generated yet.",
};

// Mock the api module
vi.mock("../api", () => ({
  refreshInsights: vi.fn().mockResolvedValue({ message: "Refresh started" }),
}));

vi.mock("react-hot-toast", () => ({
  default: Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

function renderInsights(user: User, fetchResponse: InsightsResponse) {
  // Mock global fetch for useApi
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(fetchResponse),
  });
  vi.stubGlobal("fetch", fetchMock);

  const noop = () => {};
  render(
    <AuthContext.Provider
      value={{
        token: "test-token",
        user,
        login: noop,
        logout: noop,
        isAdmin: user.role === "admin",
        loading: false,
      }}
    >
      <MemoryRouter>
        <InsightsPage />
      </MemoryRouter>
    </AuthContext.Provider>,
  );

  return fetchMock;
}

describe("InsightsPage", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("renders insights data", async () => {
    renderInsights(adminUser, mockInsights);
    expect(
      await screen.findByText("SOC2 export requests"),
    ).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(
      screen.getByText("12 mentions across email and call sources."),
    ).toBeInTheDocument();
  });

  it("shows stale warning when insights are stale", async () => {
    renderInsights(adminUser, staleInsights);
    expect(
      await screen.findByText(/insights may be outdated/i),
    ).toBeInTheDocument();
  });

  it("shows empty state when no insights exist", async () => {
    renderInsights(adminUser, emptyInsights);
    expect(
      await screen.findByText("No insights generated yet."),
    ).toBeInTheDocument();
  });

  it("shows Refresh button for admin", async () => {
    renderInsights(adminUser, mockInsights);
    expect(
      await screen.findByRole("button", { name: /refresh insights/i }),
    ).toBeInTheDocument();
  });

  it("hides Refresh button for member", async () => {
    const memberUser: User = { ...adminUser, role: "member" };
    renderInsights(memberUser, mockInsights);
    await screen.findByText("SOC2 export requests");
    expect(
      screen.queryByRole("button", { name: /refresh insights/i }),
    ).not.toBeInTheDocument();
  });

  it("starts polling on refresh click and stops when generated_at changes", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const toast = await import("react-hot-toast");
    const toastSuccess = vi.mocked(toast.default.success);

    const fetchMock = renderInsights(adminUser, mockInsights);

    const refreshBtn = await screen.findByRole("button", {
      name: /refresh insights/i,
    });
    await user.click(refreshBtn);

    // After clicking refresh, simulate poll response with new generated_at
    const updatedInsights: InsightsResponse = {
      ...mockInsights,
      generated_at: "2024-06-15T11:00:00Z", // newer
    };
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(updatedInsights),
    });

    // Advance past one poll interval
    vi.advanceTimersByTime(3500);

    await waitFor(() => {
      expect(toastSuccess).toHaveBeenCalled();
    });
  });
});
