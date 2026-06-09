import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../../../src/services/authService", () => ({
  isAuthenticated: vi.fn(),
  getStoredUser: vi.fn(),
}));

import { getStoredUser, isAuthenticated } from "../../../src/services/authService";
import ProtectedRoute from "../../../src/components/auth/ProtectedRoute";

describe("ProtectedRoute", () => {
  it("redirige al login cuando no hay sesion", () => {
    isAuthenticated.mockReturnValue(false);

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/login" element={<div>login screen</div>} />
          <Route
            path="/dashboard"
            element={(
              <ProtectedRoute>
                <div>protected content</div>
              </ProtectedRoute>
            )}
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/login screen/i)).toBeInTheDocument();
  });

  it("permite el acceso cuando hay sesion", () => {
    isAuthenticated.mockReturnValue(true);
    getStoredUser.mockReturnValue({ cargo: "director" });

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>protected content</div>
        </ProtectedRoute>
      </MemoryRouter>,
    );

    expect(screen.getByText(/protected content/i)).toBeInTheDocument();
  });

  it("redirige al dashboard cuando el rol no coincide", () => {
    isAuthenticated.mockReturnValue(true);
    getStoredUser.mockReturnValue({ cargo: "estudiante" });

    render(
      <MemoryRouter initialEntries={["/cursos"]}>
        <Routes>
          <Route path="/dashboard" element={<div>dashboard screen</div>} />
          <Route
            path="/cursos"
            element={(
              <ProtectedRoute allowedRoles={["director", "docente"]}>
                <div>courses screen</div>
              </ProtectedRoute>
            )}
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/dashboard screen/i)).toBeInTheDocument();
  });
});