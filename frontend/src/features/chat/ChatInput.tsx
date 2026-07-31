import { Send } from "lucide-react";
import { FormEvent, KeyboardEvent, useState } from "react";

import { Button } from "../../components/ui/button";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";

export function ChatInput({
  onAsk,
  isAsking,
}: {
  onAsk: (question: string) => void;
  isAsking: boolean;
}) {
  const [question, setQuestion] = useState("");

  function submit() {
    if (!question.trim() || isAsking) return;
    onAsk(question);
    setQuestion("");
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    submit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      aria-label="Ask a question"
      className="flex items-end gap-2 border-t border-border p-3"
    >
      <div className="flex-1">
        <Label htmlFor="question-input" className="sr-only">
          Ask a question about your documents
        </Label>
        <Textarea
          id="question-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents…"
          disabled={isAsking}
          rows={1}
          className="min-h-10 max-h-40 resize-none py-2"
          required
        />
      </div>
      <Button
        type="submit"
        disabled={isAsking}
        size="icon"
        className="shrink-0"
        aria-label={isAsking ? "Asking…" : "Ask"}
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}
