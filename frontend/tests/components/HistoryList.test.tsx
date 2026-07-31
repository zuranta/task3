import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { HistoryList } from "../../src/components/HistoryList";
import { QueryRecord } from "../../src/services/queries";

function makeQuery(overrides: Partial<QueryRecord> = {}): QueryRecord {
  return {
    id: "q-1",
    question: "What is the return policy?",
    status: "answered",
    answer: null,
    created_at: "2026-07-31T00:00:00Z",
    ...overrides,
  };
}

describe("HistoryList", () => {
  it("shows an empty-state message rather than an error for a brand-new account", () => {
    render(<HistoryList queries={[]} onSelect={vi.fn()} />);

    expect(screen.getByText(/haven't asked any questions yet/i)).toBeInTheDocument();
  });

  it("renders each query's question and status", () => {
    const queries = [
      makeQuery({ id: "q-1", question: "What is the return policy?", status: "answered" }),
      makeQuery({ id: "q-2", question: "What color is the sky?", status: "no_answer_found" }),
    ];

    render(<HistoryList queries={queries} onSelect={vi.fn()} />);

    expect(screen.getByText("What is the return policy?")).toBeInTheDocument();
    expect(screen.getByText(/answered/)).toBeInTheDocument();
    expect(screen.getByText("What color is the sky?")).toBeInTheDocument();
    expect(screen.getByText(/no_answer_found/)).toBeInTheDocument();
  });

  it("calls onSelect with the clicked query's id", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <HistoryList
        queries={[makeQuery({ id: "q-42", question: "Pick me" })]}
        onSelect={onSelect}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Pick me" }));

    expect(onSelect).toHaveBeenCalledWith("q-42");
  });
});
