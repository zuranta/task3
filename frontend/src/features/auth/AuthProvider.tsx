import { ReactNode, useState } from "react";

import * as authApi from "./auth";
import { AuthContext } from "./auth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => authApi.getToken() !== null);
  const [isAdmin, setIsAdmin] = useState(() => authApi.getRole() === "admin");

  async function handleRegister(email: string, username: string, password: string) {
    const token = await authApi.register(email, username, password);
    authApi.saveToken(token.access_token);
    setIsAuthenticated(true);
    setIsAdmin(authApi.getRole() === "admin");
  }

  async function handleLogin(identifier: string, password: string) {
    const token = await authApi.login(identifier, password);
    authApi.saveToken(token.access_token);
    setIsAuthenticated(true);
    setIsAdmin(authApi.getRole() === "admin");
  }

  function handleLogout() {
    authApi.clearToken();
    setIsAuthenticated(false);
    setIsAdmin(false);
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isAdmin,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
