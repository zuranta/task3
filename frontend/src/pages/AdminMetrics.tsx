import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { OperationalMetrics, getOperationalMetrics } from "../services/adminMetrics";
import { ApiError } from "../services/auth";

const STAGE_ORDER = ["upload", "retrieval", "generation"];

export function AdminMetrics() {
  const [windowMinutes, setWindowMinutes] = useState(60);
  const [metrics, setMetrics] = useState<OperationalMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void refreshMetrics(windowMinutes);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [windowMinutes]);

  async function refreshMetrics(minutes: number) {
    try {
      setError(null);
      setMetrics(await getOperationalMetrics(minutes));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load operational metrics.");
    }
  }

  const stages = metrics
    ? [
        ...STAGE_ORDER.filter((stage) => stage in metrics.by_stage),
        ...Object.keys(metrics.by_stage).filter((stage) => !STAGE_ORDER.includes(stage)),
      ]
    : [];

  return (
    <main>
      <h1>Admin: Operational Metrics</h1>
      <Link to="/">Back to Workspace</Link>

      {error && <p role="alert">{error}</p>}

      <section>
        <label htmlFor="window-minutes">Time window (minutes)</label>
        <input
          id="window-minutes"
          type="number"
          min={1}
          max={1440}
          value={windowMinutes}
          onChange={(e) => setWindowMinutes(Number(e.target.value) || 1)}
        />
        <button type="button" onClick={() => refreshMetrics(windowMinutes)}>
          Refresh
        </button>
      </section>

      <section>
        {!metrics ? (
          <p>Loading…</p>
        ) : stages.length === 0 ? (
          <p>No request traffic in the last {metrics.window_minutes} minute(s).</p>
        ) : (
          <table aria-label="Operational metrics by stage">
            <thead>
              <tr>
                <th>Stage</th>
                <th>Requests</th>
                <th>Errors</th>
                <th>Error rate</th>
                <th>p50 latency (ms)</th>
                <th>p95 latency (ms)</th>
                <th>Total tokens</th>
              </tr>
            </thead>
            <tbody>
              {stages.map((stage) => {
                const stageMetrics = metrics.by_stage[stage];
                return (
                  <tr key={stage}>
                    <td>{stage}</td>
                    <td>{stageMetrics.request_count}</td>
                    <td>{stageMetrics.error_count}</td>
                    <td>{(stageMetrics.error_rate * 100).toFixed(1)}%</td>
                    <td>{stageMetrics.p50_latency_ms.toFixed(0)}</td>
                    <td>{stageMetrics.p95_latency_ms.toFixed(0)}</td>
                    <td>{stageMetrics.total_tokens}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
