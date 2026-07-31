import { Trash2 } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { ComparisonRun } from "./adminEval";

function scorePair(a: number | undefined, b: number | undefined): string {
  return `${a?.toFixed(2) ?? "—"} / ${b?.toFixed(2) ?? "—"}`;
}

const STATUS_VARIANT: Record<ComparisonRun["status"], "default" | "secondary" | "destructive"> = {
  running: "secondary",
  completed: "default",
  partial: "destructive",
};

export function AdminDashboard({
  runs,
  selectedIds,
  onToggleSelect,
  onDeleteOne,
}: {
  runs: ComparisonRun[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onDeleteOne: (id: string) => void;
}) {
  if (runs.length === 0) {
    return <p className="text-sm text-muted-foreground">No comparison runs yet.</p>;
  }

  return (
    <Table aria-label="Comparison runs">
      <TableHeader>
        <TableRow>
          <TableHead></TableHead>
          <TableHead>Version A</TableHead>
          <TableHead>Version B</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Winner</TableHead>
          <TableHead>Correctness (A/B)</TableHead>
          <TableHead>Relevance (A/B)</TableHead>
          <TableHead>Groundedness (A/B)</TableHead>
          <TableHead></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {runs.map((run) => (
          <TableRow key={run.id}>
            <TableCell>
              <input
                type="checkbox"
                aria-label={`Select comparison run ${run.version_a_label} vs ${run.version_b_label}`}
                checked={selectedIds.has(run.id)}
                onChange={() => onToggleSelect(run.id)}
              />
            </TableCell>
            <TableCell>{run.version_a_label}</TableCell>
            <TableCell>{run.version_b_label}</TableCell>
            <TableCell>
              <Badge variant={STATUS_VARIANT[run.status]}>{run.status}</Badge>
            </TableCell>
            <TableCell>{run.winner ?? "—"}</TableCell>
            <TableCell>
              {scorePair(run.aggregate_score_a?.correctness, run.aggregate_score_b?.correctness)}
            </TableCell>
            <TableCell>
              {scorePair(run.aggregate_score_a?.relevance, run.aggregate_score_b?.relevance)}
            </TableCell>
            <TableCell>
              {scorePair(run.aggregate_score_a?.groundedness, run.aggregate_score_b?.groundedness)}
            </TableCell>
            <TableCell>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Delete comparison run ${run.version_a_label} vs ${run.version_b_label}`}
                onClick={() => onDeleteOne(run.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
