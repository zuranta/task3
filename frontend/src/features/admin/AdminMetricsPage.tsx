import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Alert, AlertDescription } from "../../components/ui/alert";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Skeleton } from "../../components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { ApiError } from "../auth/auth";
import { OperationalMetrics, getOperationalMetrics } from "./adminMetrics";

const STAGE_ORDER = ["upload", "retrieval", "generation"];

export function AdminMetricsPage() {
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

      <h1 className="text-2xl font-semibold">Admin: Operational Metrics</h1>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 pt-6">
          <div className="space-y-2">
            <Label htmlFor="window-minutes">Time window (minutes)</Label>
            <Input
              id="window-minutes"
              type="number"
              min={1}
              max={1440}
              value={windowMinutes}
              onChange={(e) => setWindowMinutes(Number(e.target.value) || 1)}
              className="w-32"
            />
          </div>
          <Button type="button" variant="secondary" onClick={() => refreshMetrics(windowMinutes)}>
            Refresh
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">By request stage</CardTitle>
        </CardHeader>
        <CardContent>
          {!metrics ? (
            <div className="space-y-2" aria-label="Loading operational metrics">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : stages.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No request traffic in the last {metrics.window_minutes} minute(s).
            </p>
          ) : (
            <Table aria-label="Operational metrics by stage">
              <TableHeader>
                <TableRow>
                  <TableHead>Stage</TableHead>
                  <TableHead>Requests</TableHead>
                  <TableHead>Errors</TableHead>
                  <TableHead>Error rate</TableHead>
                  <TableHead>p50 latency (ms)</TableHead>
                  <TableHead>p95 latency (ms)</TableHead>
                  <TableHead>Total tokens</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stages.map((stage) => {
                  const stageMetrics = metrics.by_stage[stage];
                  return (
                    <TableRow key={stage}>
                      <TableCell className="font-medium capitalize">{stage}</TableCell>
                      <TableCell>{stageMetrics.request_count}</TableCell>
                      <TableCell>{stageMetrics.error_count}</TableCell>
                      <TableCell>{(stageMetrics.error_rate * 100).toFixed(1)}%</TableCell>
                      <TableCell>{stageMetrics.p50_latency_ms.toFixed(0)}</TableCell>
                      <TableCell>{stageMetrics.p95_latency_ms.toFixed(0)}</TableCell>
                      <TableCell>{stageMetrics.total_tokens}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
