import { useNavigate } from "react-router-dom";

import { RegisterForm } from "../components/RegisterForm";

export function Register() {
  const navigate = useNavigate();

  return (
    <main>
      <h1>Create your account</h1>
      <RegisterForm onSuccess={() => navigate("/")} />
      <p>
        Already have an account? <a href="/login">Log in</a>
      </p>
    </main>
  );
}
