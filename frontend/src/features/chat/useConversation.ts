import { useCallback, useRef, useState } from "react";

import { ApiError } from "../auth/auth";
import { askQuestion } from "../query/queries";
import { ChatMessage } from "./types";

const NO_ANSWER_TEXT = "No grounded answer was found in your documents for that question.";

/**
 * Owns the chat conversation's message list. Submitting a question appends
 * a user message plus a pending assistant placeholder (which renders the
 * typing indicator, FR-034) immediately, then updates that placeholder in
 * place once POST /queries resolves (research.md §15) - never re-runs
 * generation on replay and never has more than one pending message at a
 * time, since a new question can't be submitted while one is in flight.
 */
export function useConversation() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const nextId = useRef(0);

  const isPending = messages.some((message) => message.status === "pending");

  const sendQuestion = useCallback(async (question: string) => {
    const userMessage: ChatMessage = {
      id: `msg-${nextId.current++}`,
      role: "user",
      content: question,
      timestamp: new Date().toISOString(),
      status: "complete",
    };
    const pendingId = `msg-${nextId.current++}`;
    const assistantPlaceholder: ChatMessage = {
      id: pendingId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      status: "pending",
    };

    setMessages((current) => [...current, userMessage, assistantPlaceholder]);

    try {
      const record = await askQuestion(question);
      const answer = record.answer;
      setMessages((current) =>
        current.map((message) =>
          message.id === pendingId
            ? {
                ...message,
                status: "complete",
                content:
                  answer?.status === "no_answer_found" || !answer?.answer_text
                    ? NO_ANSWER_TEXT
                    : answer.answer_text,
                citations: answer?.citations ?? [],
              }
            : message,
        ),
      );
    } catch (err) {
      setMessages((current) =>
        current.map((message) =>
          message.id === pendingId
            ? {
                ...message,
                status: "error",
                content:
                  err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
              }
            : message,
        ),
      );
    }
  }, []);

  return { messages, sendQuestion, isPending };
}
