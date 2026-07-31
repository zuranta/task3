import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { AnswerCard } from "../components/AnswerCard";
import { ChatInput } from "../components/ChatInput";
import { DocumentUpload } from "../components/DocumentUpload";
import { ApiError, useAuth } from "../services/auth";
import { DocumentRecord, deleteDocument, listDocuments } from "../services/documents";
import { QueryRecord, askQuestion } from "../services/queries";

export function Workspace() {
  const { logout, isAdmin } = useAuth();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [currentQuery, setCurrentQuery] = useState<QueryRecord | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void refreshDocuments();
  }, []);

  async function refreshDocuments() {
    try {
      setDocuments(await listDocuments());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load your documents.");
    }
  }

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

  async function handleDelete(documentId: string) {
    setError(null);
    try {
      await deleteDocument(documentId);
      await refreshDocuments();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the document.");
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
        <h2>Your documents</h2>
        <DocumentUpload onUploaded={() => refreshDocuments()} />
        <ul aria-label="Your documents">
          {documents
            .filter((doc) => doc.status !== "deleted")
            .map((doc) => (
              <li key={doc.id}>
                {doc.original_filename} — {doc.status}
                {doc.failure_reason && <span> ({doc.failure_reason})</span>}
                <button type="button" onClick={() => handleDelete(doc.id)}>
                  Delete
                </button>
              </li>
            ))}
        </ul>
      </section>

      <section>
        <h2>Ask a question</h2>
        <ChatInput onAsk={handleAsk} isAsking={isAsking} />
        {currentQuery?.answer && <AnswerCard answer={currentQuery.answer} />}
      </section>
    </main>
  );
}
