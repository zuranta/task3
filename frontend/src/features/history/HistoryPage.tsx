import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Alert, AlertDescription } from "../../components/ui/alert";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Skeleton } from "../../components/ui/skeleton";
import { ApiError } from "../auth/auth";
import { CitationBadgeList } from "../query/CitationBadge";
import { QueryRecord, getQuery, listQueryHistory } from "../query/queries";
import { HistoryList } from "./HistoryList";

export function HistoryPage() {
  const [queries, setQueries] = useState<QueryRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected] = useState<QueryRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listQueryHistory()
      .then(setQueries)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load your history.");
      })
      .finally(() => setIsLoading(false));
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
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 p-4 sm:p-6">
      <div className="flex items-center gap-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to chat
        </Link>
      </div>

      <h1 className="text-2xl font-semibold">History</h1>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <section>
        {isLoading ? (
          <div className="space-y-2" aria-label="Loading your history">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : (
          <HistoryList queries={queries} onSelect={handleSelect} />
        )}
      </section>

      {selected && (
        <Card aria-label="Selected question">
          <CardHeader>
            <CardTitle className="text-lg">{selected.question}</CardTitle>
          </CardHeader>
          {selected.answer && (
            <CardContent>
              {selected.answer.status === "no_answer_found" ? (
                <Badge variant="secondary">No grounded answer was found in your documents.</Badge>
              ) : (
                <>
                  <p className="whitespace-pre-wrap text-sm">{selected.answer.answer_text}</p>
                  <CitationBadgeList citations={selected.answer.citations} />
                </>
              )}
            </CardContent>
          )}
        </Card>
      )}
    </main>
  );
}
