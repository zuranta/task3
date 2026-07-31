import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../../src/features/auth/auth";
import { useConversation } from "../../../src/features/chat/useConversation";
import * as queriesApi from "../../../src/features/query/queries";

describe("useConversation", () => {
  it("appends a user message and a pending assistant placeholder immediately on submit", async () => {
    vi.spyOn(queriesApi, "askQuestion").mockImplementation(() => new Promise(() => {}));
    const { result } = renderHook(() => useConversation());

    act(() => {
      void result.current.sendQuestion("What is the refund policy?");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]).toMatchObject({
      role: "user",
      content: "What is the refund policy?",
      status: "complete",
    });
    expect(result.current.messages[1]).toMatchObject({ role: "assistant", status: "pending" });
    expect(result.current.isPending).toBe(true);
  });

  it("resolves the pending placeholder to the complete answer with citations on success", async () => {
    vi.spyOn(queriesApi, "askQuestion").mockResolvedValue({
      id: "q1",
      question: "What is the refund policy?",
      status: "answered",
      answer: {
        status: "answered",
        answer_text: "Refunds are available within 30 days.",
        citations: [
          {
            document_id: "doc-1",
            document_filename: "policy.pdf",
            location_label: "p. 2",
            source_removed: false,
            passage_content: "Refunds must be requested within 30 days of purchase.",
          },
        ],
        metadata: {
          prompt_tokens: 10,
          completion_tokens: 5,
          total_tokens: 15,
          context_window_utilization: 0.01,
        },
      },
      created_at: "2026-07-31T00:00:00.000Z",
    });

    const { result } = renderHook(() => useConversation());

    act(() => {
      void result.current.sendQuestion("What is the refund policy?");
    });

    await waitFor(() => expect(result.current.isPending).toBe(false));

    expect(result.current.messages[1]).toMatchObject({
      role: "assistant",
      status: "complete",
      content: "Refunds are available within 30 days.",
    });
    expect(result.current.messages[1].citations).toHaveLength(1);
  });

  it("resolves the pending placeholder to an error status on failure", async () => {
    vi.spyOn(queriesApi, "askQuestion").mockRejectedValue(
      new ApiError("Retrieval is temporarily unavailable.", 502),
    );

    const { result } = renderHook(() => useConversation());

    act(() => {
      void result.current.sendQuestion("What is the refund policy?");
    });

    await waitFor(() => expect(result.current.isPending).toBe(false));

    expect(result.current.messages[1]).toMatchObject({
      role: "assistant",
      status: "error",
      content: "Retrieval is temporarily unavailable.",
    });
  });
});
