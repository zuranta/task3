import { FormEvent, useState } from "react";

export function ChatInput({
  onAsk,
  isAsking,
}: {
  onAsk: (question: string) => void;
  isAsking: boolean;
}) {
  const [question, setQuestion] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    onAsk(question);
    setQuestion("");
  }

  return (
    <form onSubmit={handleSubmit} aria-label="Ask a question">
      <label htmlFor="question-input">Ask a question about your documents</label>
      <input
        id="question-input"
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={isAsking}
        required
      />
      <button type="submit" disabled={isAsking}>
        {isAsking ? "Asking…" : "Ask"}
      </button>
    </form>
  );
}
