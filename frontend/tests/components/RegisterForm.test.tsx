import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RegisterForm } from "../../src/components/RegisterForm";
import { ApiError, AuthContext, AuthContextValue } from "../../src/services/auth";

function renderWithAuth(overrides: Partial<AuthContextValue> = {}) {
  const value: AuthContextValue = {
    isAuthenticated: false,
    isAdmin: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  };
  render(
    <AuthContext.Provider value={value}>
      <RegisterForm onSuccess={vi.fn()} />
    </AuthContext.Provider>,
  );
  return value;
}

describe("RegisterForm", () => {
  it("submits email, username, and password to register()", async () => {
    const user = userEvent.setup();
    const registerMock = vi.fn().mockResolvedValue(undefined);
    renderWithAuth({ register: registerMock });

    await user.type(screen.getByLabelText(/email/i), "alice@example.com");
    await user.type(screen.getByLabelText(/username/i), "alice");
    await user.type(screen.getByLabelText(/password/i), "correcthorse");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith("alice@example.com", "alice", "correcthorse");
    });
  });

  it("shows the error message when registration fails", async () => {
    const user = userEvent.setup();
    const registerMock = vi.fn().mockRejectedValue(new ApiError("Username already taken.", 409));
    renderWithAuth({ register: registerMock });

    await user.type(screen.getByLabelText(/email/i), "bob@example.com");
    await user.type(screen.getByLabelText(/username/i), "bob");
    await user.type(screen.getByLabelText(/password/i), "correcthorse");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Username already taken.");
  });
});
