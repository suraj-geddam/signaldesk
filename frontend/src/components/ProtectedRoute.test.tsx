import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect } from "vitest";
import { AuthContext } from "../context/AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";
import type { User } from "../types";

const testUser: User = {
  id: "u1",
  username: "tester",
  role: "member",
  created_at: "2024-01-01T00:00:00Z",
};

function renderWithAuth({
  user,
  loading,
  initialPath = "/protected",
}: {
  user: User | null;
  loading: boolean;
  initialPath?: string;
}) {
  const noop = () => {};
  return render(
    <AuthContext.Provider
      value={{
        token: user ? "test-token" : null,
        user,
        login: noop,
        logout: noop,
        isAdmin: user?.role === "admin",
        loading,
      }}
    >
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/protected" element={<div>Protected Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects to /login when unauthenticated", () => {
    renderWithAuth({ user: null, loading: false });
    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    renderWithAuth({ user: testUser, loading: false });
    expect(screen.getByText("Protected Content")).toBeInTheDocument();
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });

  it("shows spinner while loading", () => {
    renderWithAuth({ user: null, loading: true });
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
    // The spinner SVG has an animate-spin class
    const svg = document.querySelector("svg.animate-spin");
    expect(svg).toBeInTheDocument();
  });
});
