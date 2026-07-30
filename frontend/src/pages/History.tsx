import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { AnswerCard } from "../components/AnswerCard";
import { HistoryList } from "../components/HistoryList";
import { ApiError } from "../services/auth";
import { QueryRecord, getQuery, listQueryHistory } from "../services/queries";

export function History() {
  const [queries, setQueries] = useState<QueryRecord[]>([]);
  const [selected, setSelected] = useState<QueryRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listQueryHistory()
      .then(setQueries)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load your history.");
      });
  }, []);

  async function handleSelect(queryId: string) {
    setError(null);
    try {
      setSelected(await getQuery(queryId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load that question.");
    }
  }

  return (
    <main>
      <h1>History</h1>
      <Link to="/">Back to Workspace</Link>

      {error && <p role="alert">{error}</p>}

      <section>
        <HistoryList queries={queries} onSelect={handleSelect} />
      </section>

      {selected && (
        <section aria-label="Selected question">
          <h2>{selected.question}</h2>
          {selected.answer && <AnswerCard answer={selected.answer} />}
        </section>
      )}
    </main>
  );
}
