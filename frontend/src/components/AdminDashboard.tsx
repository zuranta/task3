import { ComparisonRun } from "../services/adminEval";

function scorePair(a: number | undefined, b: number | undefined): string {
  return `${a?.toFixed(2) ?? "—"} / ${b?.toFixed(2) ?? "—"}`;
}

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
    return <p>No comparison runs yet.</p>;
  }

  return (
    <table aria-label="Comparison runs">
      <thead>
        <tr>
          <th></th>
          <th>Version A</th>
          <th>Version B</th>
          <th>Status</th>
          <th>Winner</th>
          <th>Correctness (A/B)</th>
          <th>Relevance (A/B)</th>
          <th>Groundedness (A/B)</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr key={run.id}>
            <td>
              <input
                type="checkbox"
                aria-label={`Select comparison run ${run.version_a_label} vs ${run.version_b_label}`}
                checked={selectedIds.has(run.id)}
                onChange={() => onToggleSelect(run.id)}
              />
            </td>
            <td>{run.version_a_label}</td>
            <td>{run.version_b_label}</td>
            <td>{run.status}</td>
            <td>{run.winner ?? "—"}</td>
            <td>
              {scorePair(run.aggregate_score_a?.correctness, run.aggregate_score_b?.correctness)}
            </td>
            <td>{scorePair(run.aggregate_score_a?.relevance, run.aggregate_score_b?.relevance)}</td>
            <td>
              {scorePair(run.aggregate_score_a?.groundedness, run.aggregate_score_b?.groundedness)}
            </td>
            <td>
              <button type="button" onClick={() => onDeleteOne(run.id)}>
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
