import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { HistoryList } from "../../../src/features/history/HistoryList";
import { QueryRecord } from "../../../src/features/query/queries";

describe("HistoryList", () => {
  it("shows a distinct empty-state message when there is no history yet", () => {
    render(<HistoryList queries={[]} onSelect={vi.fn()} />);

    expect(screen.getByText(/haven.t asked any questions yet/i)).toBeInTheDocument();
  });

  it("lists past questions most-recent-first order as given, with a status badge each", async () => {
    const queries: QueryRecord[] = [
      {
        id: "q1",
        question: "What is the refund policy?",
        status: "answered",
        answer: null,
        created_at: "2026-07-31T00:00:00.000Z",
      },
      {
        id: "q2",
        question: "What is on the moon?",
        status: "no_answer_found",
        answer: null,
        created_at: "2026-07-30T00:00:00.000Z",
      },
    ];
    const onSelect = vi.fn();
    const user = userEvent.setup();

    render(<HistoryList queries={queries} onSelect={onSelect} />);

    expect(screen.getByText("What is the refund policy?")).toBeInTheDocument();
    expect(screen.getByText("no answer found")).toBeInTheDocument();

    await user.click(screen.getByText("What is on the moon?"));
    expect(onSelect).toHaveBeenCalledWith("q2");
  });
});
