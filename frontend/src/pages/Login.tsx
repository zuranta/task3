import { useNavigate } from "react-router-dom";

import { LoginForm } from "../components/LoginForm";

export function Login() {
  const navigate = useNavigate();

  return (
    <main>
      <h1>Log in</h1>
      <LoginForm onSuccess={() => navigate("/")} />
      <p>
        Need an account? <a href="/register">Register</a>
      </p>
    </main>
  );
}
