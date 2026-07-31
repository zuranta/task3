import { Badge } from "../../components/ui/badge";
import { QueryRecord } from "../query/queries";

const STATUS_VARIANT: Record<QueryRecord["status"], "default" | "secondary" | "destructive"> = {
  answered: "default",
  no_answer_found: "secondary",
  failed: "destructive",
};

export function HistoryList({
  queries,
  onSelect,
}: {
  queries: QueryRecord[];
  onSelect: (queryId: string) => void;
}) {
  if (queries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        You haven&apos;t asked any questions yet — ask one from the chat screen to see it here.
      </p>
    );
  }

  return (
    <ul aria-label="Query history" className="divide-y divide-border rounded-md border border-border">
      {queries.map((query) => (
        <li key={query.id}>
          <button
            type="button"
            onClick={() => onSelect(query.id)}
            className="flex w-full items-center justify-between gap-2 p-3 text-left text-sm hover:bg-accent hover:text-accent-foreground"
          >
            <span className="min-w-0 truncate">{query.question}</span>
            <Badge variant={STATUS_VARIANT[query.status]} className="shrink-0">
              {query.status.replace(/_/g, " ")}
            </Badge>
          </button>
        </li>
      ))}
    </ul>
  );
}
