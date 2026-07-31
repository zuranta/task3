import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ChatWindow } from "../../../src/features/chat/ChatWindow";
import { ChatMessage } from "../../../src/features/chat/types";

function message(overrides: Partial<ChatMessage>): ChatMessage {
  return {
    id: "msg-0",
    role: "user",
    content: "",
    timestamp: "2026-07-31T00:00:00.000Z",
    status: "complete",
    ...overrides,
  };
}

describe("ChatWindow", () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("shows an empty-state prompt when no messages exist yet", () => {
    render(<ChatWindow messages={[]} />);

    expect(screen.getByText(/ask a question about your uploaded documents/i)).toBeInTheDocument();
  });

  it("renders user and assistant bubbles in submission order", () => {
    const messages = [
      message({ id: "msg-1", role: "user", content: "What is the refund policy?" }),
      message({ id: "msg-2", role: "assistant", content: "Refunds are available within 30 days." }),
      message({ id: "msg-3", role: "user", content: "What about after 30 days?" }),
    ];

    render(<ChatWindow messages={messages} />);

    const bubbleTexts = screen.getByLabelText(/conversation/i).querySelectorAll("p")!;
    expect(Array.from(bubbleTexts).map((el) => el.textContent)).toEqual([
      "What is the refund policy?",
      "Refunds are available within 30 days.",
      "What about after 30 days?",
    ]);
  });

  it("scrolls to the latest message whenever the message list changes", () => {
    const scrollSpy = vi.fn();
    Element.prototype.scrollIntoView = scrollSpy;

    const { rerender } = render(
      <ChatWindow messages={[message({ id: "msg-1", content: "Hi" })]} />,
    );
    expect(scrollSpy).toHaveBeenCalledTimes(1);

    rerender(
      <ChatWindow
        messages={[
          message({ id: "msg-1", content: "Hi" }),
          message({ id: "msg-2", role: "assistant", content: "Hello!" }),
        ]}
      />,
    );
    expect(scrollSpy).toHaveBeenCalledTimes(2);
  });
});
