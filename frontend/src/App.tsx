import { Navigate, Route, Routes } from "react-router-dom";

import { AdminEval } from "./pages/AdminEval";
import { AdminMetrics } from "./pages/AdminMetrics";
import { History } from "./pages/History";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Workspace } from "./pages/Workspace";
import { useAuth } from "./services/auth";

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function AdminRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isAdmin } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return isAdmin ? children : <Navigate to="/" replace />;
}

function PublicOnlyRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/" replace /> : children;
}

export function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <Register />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Workspace />
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <History />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/eval"
        element={
          <AdminRoute>
            <AdminEval />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/metrics"
        element={
          <AdminRoute>
            <AdminMetrics />
          </AdminRoute>
        }
      />
    </Routes>
  );
}
