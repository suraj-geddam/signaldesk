import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { AuthContext } from "../context/AuthContext";
import { FeedbackFilterBar } from "./FeedbackFilterBar";

function renderFilterBar(initialSearch = "") {
  const initialEntries = initialSearch
    ? [`/feedback?${initialSearch}`]
    : ["/feedback"];

  const noop = () => {};
  return render(
    <AuthContext.Provider
      value={{
        token: "test-token",
        user: {
          id: "u1",
          username: "tester",
          role: "member",
          created_at: "2024-01-01T00:00:00Z",
        },
        login: noop,
        logout: noop,
        isAdmin: false,
        loading: false,
      }}
    >
      <MemoryRouter initialEntries={initialEntries}>
        <FeedbackFilterBar />
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("FeedbackFilterBar", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders all filter controls", () => {
    renderFilterBar();
    expect(
      screen.getByPlaceholderText("Search feedback..."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by status")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by priority")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by source")).toBeInTheDocument();
    expect(screen.getByLabelText("Sort order")).toBeInTheDocument();
  });

  it("shows Clear filters link when filters are active", () => {
    renderFilterBar("status=new");
    expect(screen.getByText("Clear filters")).toBeInTheDocument();
  });

  it("does not show Clear filters when no filters are active", () => {
    renderFilterBar();
    expect(screen.queryByText("Clear filters")).not.toBeInTheDocument();
  });

  it("changes status filter via select", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderFilterBar();

    const statusSelect = screen.getByLabelText(
      "Filter by status",
    ) as HTMLSelectElement;
    await user.selectOptions(statusSelect, "new");
    expect(statusSelect.value).toBe("new");
  });

  it("changes priority filter via select", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderFilterBar();

    const prioritySelect = screen.getByLabelText(
      "Filter by priority",
    ) as HTMLSelectElement;
    await user.selectOptions(prioritySelect, "high");
    expect(prioritySelect.value).toBe("high");
  });
});
