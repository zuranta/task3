import { useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../auth/auth";
import { DocumentUpload } from "../upload/DocumentUpload";
import { ChatInput } from "./ChatInput";
import { QueryRecord, askQuestion } from "../query/queries";
import { ApiError } from "../auth/auth";

export function ChatPage() {
  const { logout, isAdmin } = useAuth();
  const [currentQuery, setCurrentQuery] = useState<QueryRecord | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(question: string) {
    setError(null);
    setIsAsking(true);
    try {
      setCurrentQuery(await askQuestion(question));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main>
      <h1>Workspace</h1>
      <Link to="/history">View history</Link>
      {isAdmin && <Link to="/admin/eval">Admin: Evaluation</Link>}
      {isAdmin && <Link to="/admin/metrics">Admin: Operational Metrics</Link>}
      <button type="button" onClick={logout}>
        Log out
      </button>

      {error && <p role="alert">{error}</p>}

      <section>
        <DocumentUpload />
      </section>

      <section>
        <h2>Ask a question</h2>
        <ChatInput onAsk={handleAsk} isAsking={isAsking} />
        {currentQuery?.answer && <p>{currentQuery.answer.answer_text}</p>}
      </section>
    </main>
  );
}
