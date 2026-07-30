import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "../../src/components/LoginForm";
import { ApiError, AuthContext, AuthContextValue } from "../../src/services/auth";

function renderWithAuth(overrides: Partial<AuthContextValue> = {}) {
  const value: AuthContextValue = {
    isAuthenticated: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  };
  render(
    <AuthContext.Provider value={value}>
      <LoginForm onSuccess={vi.fn()} />
    </AuthContext.Provider>,
  );
  return value;
}

describe("LoginForm", () => {
  it("submits the identifier (email or username) and password to login()", async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockResolvedValue(undefined);
    renderWithAuth({ login: loginMock });

    await user.type(screen.getByLabelText(/email or username/i), "alice");
    await user.type(screen.getByLabelText(/^password$/i), "correcthorse");
    await user.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("alice", "correcthorse");
    });
  });

  it("shows a generic error message on invalid credentials without revealing which field was wrong", async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockRejectedValue(new ApiError("Invalid credentials.", 401));
    renderWithAuth({ login: loginMock });

    await user.type(screen.getByLabelText(/email or username/i), "alice");
    await user.type(screen.getByLabelText(/^password$/i), "wrong-password");
    await user.click(screen.getByRole("button", { name: /log in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials.");
  });
});
