import { useNavigate } from "react-router-dom";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { RegisterForm } from "./RegisterForm";

export function RegisterPage() {
  const navigate = useNavigate();

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
          <CardDescription>Upload documents and ask grounded, cited questions.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RegisterForm onSuccess={() => navigate("/")} />
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <a
              href="/login"
              className="font-medium text-primary underline-offset-4 hover:underline"
            >
              Log in
            </a>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
