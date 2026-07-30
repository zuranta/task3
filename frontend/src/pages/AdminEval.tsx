import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { AdminDashboard } from "../components/AdminDashboard";
import {
  ComparisonRun,
  addDatasetItem,
  listComparisonRuns,
  startComparisonRun,
} from "../services/adminEval";
import { ApiError } from "../services/auth";

export function AdminEval() {
  const [runs, setRuns] = useState<ComparisonRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const [question, setQuestion] = useState("");
  const [expectedAnswer, setExpectedAnswer] = useState("");
  const [versionA, setVersionA] = useState("");
  const [versionB, setVersionB] = useState("");

  useEffect(() => {
    void refreshRuns();
  }, []);

  async function refreshRuns() {
    try {
      setRuns(await listComparisonRuns());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load comparison runs.");
    }
  }

  async function handleAddDatasetItem(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await addDatasetItem({
        question,
        expected_answer: expectedAnswer,
        expected_source_reference: null,
      });
      setQuestion("");
      setExpectedAnswer("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add the dataset item.");
    }
  }

  async function handleStartRun(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsStarting(true);
    try {
      await startComparisonRun(versionA, versionB);
      setVersionA("");
      setVersionB("");
      await refreshRuns();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start the comparison run.");
    } finally {
      setIsStarting(false);
    }
  }

  return (
    <main>
      <h1>Admin: Evaluation</h1>
      <Link to="/">Back to Workspace</Link>

      {error && <p role="alert">{error}</p>}

      <section>
        <h2>Add benchmark question</h2>
        <form onSubmit={handleAddDatasetItem} aria-label="Add dataset item">
          <label htmlFor="dataset-question">Question</label>
          <input
            id="dataset-question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
          />
          <label htmlFor="dataset-expected-answer">Expected answer</label>
          <input
            id="dataset-expected-answer"
            value={expectedAnswer}
            onChange={(e) => setExpectedAnswer(e.target.value)}
            required
          />
          <button type="submit">Add</button>
        </form>
      </section>

      <section>
        <h2>Run a comparison</h2>
        <form onSubmit={handleStartRun} aria-label="Start comparison run">
          <label htmlFor="version-a">Version A label</label>
          <input
            id="version-a"
            value={versionA}
            onChange={(e) => setVersionA(e.target.value)}
            required
          />
          <label htmlFor="version-b">Version B label</label>
          <input
            id="version-b"
            value={versionB}
            onChange={(e) => setVersionB(e.target.value)}
            required
          />
          <button type="submit" disabled={isStarting}>
            {isStarting ? "Running…" : "Run comparison"}
          </button>
        </form>
      </section>

      <section>
        <h2>Past comparison runs</h2>
        <AdminDashboard runs={runs} />
      </section>
    </main>
  );
}
