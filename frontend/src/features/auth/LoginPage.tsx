import { useNavigate } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { LoginForm } from "./LoginForm";

export function LoginPage() {
  const navigate = useNavigate();

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Log in</CardTitle>
          <CardDescription>Access your documents, questions, and answers.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <LoginForm onSuccess={() => navigate("/")} />
          <p className="text-center text-sm text-muted-foreground">
            Need an account?{" "}
            <a href="/register" className="font-medium text-primary underline-offset-4 hover:underline">
              Register
            </a>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
