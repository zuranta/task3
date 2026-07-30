import { ComparisonRun } from "../services/adminEval";

function scorePair(a: number | undefined, b: number | undefined): string {
  return `${a?.toFixed(2) ?? "—"} / ${b?.toFixed(2) ?? "—"}`;
}

export function AdminDashboard({ runs }: { runs: ComparisonRun[] }) {
  if (runs.length === 0) {
    return <p>No comparison runs yet.</p>;
  }

  return (
    <table aria-label="Comparison runs">
      <thead>
        <tr>
          <th>Version A</th>
          <th>Version B</th>
          <th>Status</th>
          <th>Winner</th>
          <th>Correctness (A/B)</th>
          <th>Relevance (A/B)</th>
          <th>Groundedness (A/B)</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr key={run.id}>
            <td>{run.version_a_label}</td>
            <td>{run.version_b_label}</td>
            <td>{run.status}</td>
            <td>{run.winner ?? "—"}</td>
            <td>
              {scorePair(run.aggregate_score_a?.correctness, run.aggregate_score_b?.correctness)}
            </td>
            <td>
              {scorePair(run.aggregate_score_a?.relevance, run.aggregate_score_b?.relevance)}
            </td>
            <td>
              {scorePair(
                run.aggregate_score_a?.groundedness,
                run.aggregate_score_b?.groundedness,
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
