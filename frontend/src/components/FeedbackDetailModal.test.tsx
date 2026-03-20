import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AuthContext } from "../context/AuthContext";
import { FeedbackDetailModal } from "./FeedbackDetailModal";
import type { Feedback, User } from "../types";

vi.mock("../api", () => ({
  updateFeedback: vi.fn().mockResolvedValue({}),
}));

vi.mock("react-hot-toast", () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockFeedback: Feedback = {
  id: "fb1",
  title: "Test feedback",
  description: "This is a detailed description of the feedback.",
  source: "email",
  priority: "high",
  status: "new",
  created_by: "u1",
  idempotency_key: null,
  created_at: "2024-06-15T10:00:00Z",
  updated_at: "2024-06-15T12:00:00Z",
};

const ownerUser: User = {
  id: "u1",
  username: "owner",
  role: "member",
  created_at: "2024-01-01T00:00:00Z",
};

const otherUser: User = {
  id: "u2",
  username: "other",
  role: "member",
  created_at: "2024-01-01T00:00:00Z",
};

const adminUser: User = {
  id: "u3",
  username: "admin",
  role: "admin",
  created_at: "2024-01-01T00:00:00Z",
};

function renderModal(user: User) {
  const noop = () => {};
  return render(
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
      <FeedbackDetailModal
        feedback={mockFeedback}
        onClose={noop}
        onUpdated={noop}
      />
    </AuthContext.Provider>,
  );
}

describe("FeedbackDetailModal", () => {
  it("renders in view mode by default", () => {
    renderModal(ownerUser);
    expect(screen.getByText("Test feedback")).toBeInTheDocument();
    expect(
      screen.getByText("This is a detailed description of the feedback."),
    ).toBeInTheDocument();
    expect(screen.getByText("New")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("shows Edit button for the feedback owner", () => {
    renderModal(ownerUser);
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
  });

  it("hides Edit button for non-owner members", () => {
    renderModal(otherUser);
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
  });

  it("shows Edit button for admins regardless of ownership", () => {
    renderModal(adminUser);
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
  });

  it("switches to edit mode and pre-fills form", async () => {
    const user = userEvent.setup();
    renderModal(ownerUser);

    await user.click(screen.getByRole("button", { name: "Edit" }));

    // Now in edit mode — form fields should be pre-filled
    const titleInput = screen.getByLabelText("Title") as HTMLInputElement;
    expect(titleInput.value).toBe("Test feedback");

    const descInput = screen.getByLabelText("Description") as HTMLTextAreaElement;
    expect(descInput.value).toBe(
      "This is a detailed description of the feedback.",
    );

    // Selects should be pre-filled
    const sourceSelect = screen.getByLabelText("Source") as HTMLSelectElement;
    expect(sourceSelect.value).toBe("email");

    const prioritySelect = screen.getByLabelText("Priority") as HTMLSelectElement;
    expect(prioritySelect.value).toBe("high");

    const statusSelect = screen.getByLabelText("Status") as HTMLSelectElement;
    expect(statusSelect.value).toBe("new");
  });

  it("returns to view mode on Cancel in edit mode", async () => {
    const user = userEvent.setup();
    renderModal(ownerUser);

    await user.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByLabelText("Title")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    // Back in view mode — no input fields
    expect(screen.queryByLabelText("Title")).not.toBeInTheDocument();
    expect(screen.getByText("Test feedback")).toBeInTheDocument();
  });
});
