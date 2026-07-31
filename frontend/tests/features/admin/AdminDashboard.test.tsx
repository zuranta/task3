import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AdminDashboard } from "../../../src/features/admin/AdminDashboard";
import { ComparisonRun } from "../../../src/features/admin/adminEval";

function makeRun(overrides: Partial<ComparisonRun> = {}): ComparisonRun {
  return {
    id: "run-1",
    version_a_label: "v1",
    version_b_label: "v2",
    status: "completed",
    aggregate_score_a: { correctness: 1, relevance: 1, groundedness: 1 },
    aggregate_score_b: { correctness: 0.5, relevance: 0.5, groundedness: 0.5 },
    winner: "a",
    started_at: "2026-07-31T00:00:00Z",
    completed_at: "2026-07-31T00:01:00Z",
    ...overrides,
  };
}

describe("AdminDashboard", () => {
  it("shows a message rather than an empty table when there are no runs yet", () => {
    render(
      <AdminDashboard
        runs={[]}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onDeleteOne={vi.fn()}
      />,
    );

    expect(screen.getByText(/no comparison runs yet/i)).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("renders each run's labels, status, winner, and scores", () => {
    render(
      <AdminDashboard
        runs={[makeRun()]}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onDeleteOne={vi.fn()}
      />,
    );

    expect(screen.getByText("v1")).toBeInTheDocument();
    expect(screen.getByText("v2")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("a")).toBeInTheDocument();
    // All three score columns share the same fixture values (correctness/
    // relevance/groundedness), so all three render identical text.
    expect(screen.getAllByText("1.00 / 0.50")).toHaveLength(3);
  });

  it("renders a dash for missing aggregate scores instead of crashing (a running/partial run)", () => {
    render(
      <AdminDashboard
        runs={[
          makeRun({
            status: "running",
            aggregate_score_a: null,
            aggregate_score_b: null,
            winner: null,
          }),
        ]}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onDeleteOne={vi.fn()}
      />,
    );

    expect(screen.getAllByText("— / —").length).toBeGreaterThan(0);
    expect(screen.getByText("—", { selector: "td" })).toBeInTheDocument();
  });

  it("reflects selectedIds on the row checkbox and calls onToggleSelect with the run's id", async () => {
    const user = userEvent.setup();
    const onToggleSelect = vi.fn();
    render(
      <AdminDashboard
        runs={[makeRun({ id: "run-7" })]}
        selectedIds={new Set(["run-7"])}
        onToggleSelect={onToggleSelect}
        onDeleteOne={vi.fn()}
      />,
    );

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();

    await user.click(checkbox);

    expect(onToggleSelect).toHaveBeenCalledWith("run-7");
  });

  it("calls onDeleteOne with the run's id when its delete button is clicked", async () => {
    const user = userEvent.setup();
    const onDeleteOne = vi.fn();
    render(
      <AdminDashboard
        runs={[makeRun({ id: "run-9" })]}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onDeleteOne={onDeleteOne}
      />,
    );

    await user.click(screen.getByRole("button", { name: /delete/i }));

    expect(onDeleteOne).toHaveBeenCalledWith("run-9");
  });
});
