import { ArrowLeft, Loader2, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Alert, AlertDescription } from "../../components/ui/alert";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { ApiError } from "../auth/auth";
import { AdminDashboard } from "./AdminDashboard";
import {
  ComparisonRun,
  DatasetItem,
  addDatasetItem,
  deleteComparisonRuns,
  deleteDatasetItems,
  listComparisonRuns,
  listDatasetItems,
  startComparisonRun,
} from "./adminEval";

function toggleId(ids: Set<string>, id: string): Set<string> {
  const next = new Set(ids);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  return next;
}

export function AdminEvalPage() {
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
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 p-4 sm:p-6">
      <div className="flex items-center gap-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to chat
        </Link>
      </div>

      <h1 className="text-2xl font-semibold">Admin: Evaluation</h1>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Add benchmark question</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddDatasetItem} aria-label="Add dataset item" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="dataset-question">Question</Label>
              <Input
                id="dataset-question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dataset-expected-answer">Expected answer</Label>
              <Input
                id="dataset-expected-answer"
                value={expectedAnswer}
                onChange={(e) => setExpectedAnswer(e.target.value)}
                required
              />
            </div>
            <Button type="submit">Add</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Benchmark questions ({datasetItems.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {datasetItems.length === 0 ? (
            <p className="text-sm text-muted-foreground">No benchmark questions yet.</p>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={selectedItemIds.size === 0}
                onClick={() => handleDeleteDatasetItems(Array.from(selectedItemIds))}
              >
                <Trash2 className="h-4 w-4" />
                Delete selected ({selectedItemIds.size})
              </Button>
              <Table aria-label="Benchmark questions">
                <TableHeader>
                  <TableRow>
                    <TableHead>
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
                    </TableHead>
                    <TableHead>Question</TableHead>
                    <TableHead>Expected answer</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {datasetItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          aria-label={`Select benchmark question: ${item.question}`}
                          checked={selectedItemIds.has(item.id)}
                          onChange={() =>
                            setSelectedItemIds((current) => toggleId(current, item.id))
                          }
                        />
                      </TableCell>
                      <TableCell>{item.question}</TableCell>
                      <TableCell>{item.expected_answer}</TableCell>
                      <TableCell>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          aria-label={`Delete benchmark question: ${item.question}`}
                          onClick={() => handleDeleteDatasetItems([item.id])}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </>
          )}
          <p className="text-sm text-muted-foreground">
            A comparison run below is scored against every question listed here.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Run a comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleStartRun} aria-label="Start comparison run" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="version-a">Version A label</Label>
              <Input
                id="version-a"
                value={versionA}
                onChange={(e) => setVersionA(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="version-b">Version B label</Label>
              <Input
                id="version-b"
                value={versionB}
                onChange={(e) => setVersionB(e.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={isStarting}>
              {isStarting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isStarting ? "Running…" : "Run comparison"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Past comparison runs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {runs.length > 0 && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={selectedRunIds.size === 0}
              onClick={() => handleDeleteComparisonRuns(Array.from(selectedRunIds))}
            >
              <Trash2 className="h-4 w-4" />
              Delete selected ({selectedRunIds.size})
            </Button>
          )}
          <AdminDashboard
            runs={runs}
            selectedIds={selectedRunIds}
            onToggleSelect={(id) => setSelectedRunIds((current) => toggleId(current, id))}
            onDeleteOne={(id) => handleDeleteComparisonRuns([id])}
          />
        </CardContent>
      </Card>
    </main>
  );
}
