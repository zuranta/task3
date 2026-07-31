import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { AdminDashboard } from "../components/AdminDashboard";
import {
  ComparisonRun,
  DatasetItem,
  addDatasetItem,
  deleteComparisonRuns,
  deleteDatasetItems,
  listComparisonRuns,
  listDatasetItems,
  startComparisonRun,
} from "../services/adminEval";
import { ApiError } from "../services/auth";

function toggleId(ids: Set<string>, id: string): Set<string> {
  const next = new Set(ids);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  return next;
}

export function AdminEval() {
  const [runs, setRuns] = useState<ComparisonRun[]>([]);
  const [datasetItems, setDatasetItems] = useState<DatasetItem[]>([]);
  const [selectedItemIds, setSelectedItemIds] = useState<Set<string>>(new Set());
  const [selectedRunIds, setSelectedRunIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const [question, setQuestion] = useState("");
  const [expectedAnswer, setExpectedAnswer] = useState("");
  const [versionA, setVersionA] = useState("");
  const [versionB, setVersionB] = useState("");

  useEffect(() => {
    void refreshRuns();
    void refreshDatasetItems();
  }, []);

  async function refreshRuns() {
    try {
      setRuns(await listComparisonRuns());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load comparison runs.");
    }
  }

  async function refreshDatasetItems() {
    try {
      setDatasetItems(await listDatasetItems());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load benchmark questions.");
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
      await refreshDatasetItems();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add the dataset item.");
    }
  }

  async function handleDeleteDatasetItems(ids: string[]) {
    setError(null);
    try {
      await deleteDatasetItems(ids);
      setSelectedItemIds((current) => {
        const next = new Set(current);
        ids.forEach((id) => next.delete(id));
        return next;
      });
      await refreshDatasetItems();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not delete the benchmark question(s).",
      );
    }
  }

  async function handleDeleteComparisonRuns(ids: string[]) {
    setError(null);
    try {
      await deleteComparisonRuns(ids);
      setSelectedRunIds((current) => {
        const next = new Set(current);
        ids.forEach((id) => next.delete(id));
        return next;
      });
      await refreshRuns();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the comparison run(s).");
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
        <h2>Benchmark questions ({datasetItems.length})</h2>
        {datasetItems.length === 0 ? (
          <p>No benchmark questions yet.</p>
        ) : (
          <>
            <button
              type="button"
              disabled={selectedItemIds.size === 0}
              onClick={() => handleDeleteDatasetItems(Array.from(selectedItemIds))}
            >
              Delete selected ({selectedItemIds.size})
            </button>
            <table aria-label="Benchmark questions">
              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      aria-label="Select all benchmark questions"
                      checked={selectedItemIds.size === datasetItems.length}
                      onChange={(e) =>
                        setSelectedItemIds(
                          e.target.checked
                            ? new Set(datasetItems.map((item) => item.id))
                            : new Set(),
                        )
                      }
                    />
                  </th>
                  <th>Question</th>
                  <th>Expected answer</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {datasetItems.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Select benchmark question: ${item.question}`}
                        checked={selectedItemIds.has(item.id)}
                        onChange={() => setSelectedItemIds((current) => toggleId(current, item.id))}
                      />
                    </td>
                    <td>{item.question}</td>
                    <td>{item.expected_answer}</td>
                    <td>
                      <button type="button" onClick={() => handleDeleteDatasetItems([item.id])}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
        <p>A comparison run below is scored against every question listed here.</p>
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
        {runs.length > 0 && (
          <button
            type="button"
            disabled={selectedRunIds.size === 0}
            onClick={() => handleDeleteComparisonRuns(Array.from(selectedRunIds))}
          >
            Delete selected ({selectedRunIds.size})
          </button>
        )}
        <AdminDashboard
          runs={runs}
          selectedIds={selectedRunIds}
          onToggleSelect={(id) => setSelectedRunIds((current) => toggleId(current, id))}
          onDeleteOne={(id) => handleDeleteComparisonRuns([id])}
        />
      </section>
    </main>
  );
}
