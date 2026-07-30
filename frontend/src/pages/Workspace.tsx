import { useAuth } from "../services/auth";

// Placeholder for User Story 1 routing; User Story 2 replaces this with the real
// upload + ask workspace (frontend/src/pages/Workspace.tsx, task T061).
export function Workspace() {
  const { logout } = useAuth();

  return (
    <main>
      <h1>Workspace</h1>
      <p>You are logged in.</p>
      <button type="button" onClick={logout}>
        Log out
      </button>
    </main>
  );
}
