import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChatBubble } from "../../../src/features/chat/ChatBubble";
import { ChatMessage } from "../../../src/features/chat/types";

describe("ChatBubble", () => {
  it("renders an animated typing indicator for a pending assistant message", () => {
    const message: ChatMessage = {
      id: "msg-1",
      role: "assistant",
      content: "",
      timestamp: "2026-07-31T00:00:00.000Z",
      status: "pending",
    };

    render(<ChatBubble message={message} />);

    expect(screen.getByRole("status", { name: /assistant is thinking/i })).toBeInTheDocument();
  });

  it("renders citations in a visually distinct style from the answer text", () => {
    const message: ChatMessage = {
      id: "msg-2",
      role: "assistant",
      content: "Refunds are available within 30 days.",
      citations: [
        {
          document_id: "doc-1",
          document_filename: "policy.pdf",
          location_label: "p. 2",
          source_removed: false,
          passage_content: "Refunds must be requested within 30 days of purchase.",
        },
      ],
      timestamp: "2026-07-31T00:00:00.000Z",
      status: "complete",
    };

    render(<ChatBubble message={message} />);

    const answerText = screen.getByText("Refunds are available within 30 days.");
    const citation = screen.getByText(/policy\.pdf/);

    // The citation must not share the answer text's element/class — it renders
    // inside its own citation-badge markup (FR-031).
    expect(citation).not.toBe(answerText);
    expect(citation.className).not.toBe(answerText.className);
    expect(citation.closest("ul")).toHaveAttribute("aria-label", "Citations");
  });

  it("renders a distinct styled error state instead of raw error text", () => {
    const message: ChatMessage = {
      id: "msg-3",
      role: "assistant",
      content: "Something went wrong. Please try again.",
      timestamp: "2026-07-31T00:00:00.000Z",
      status: "error",
    };

    render(<ChatBubble message={message} />);

    expect(screen.getByText("Something went wrong", { exact: true })).toBeInTheDocument();
    expect(screen.getByText("Something went wrong. Please try again.")).toBeInTheDocument();
  });
});
