export function TypingIndicator() {
  return (
    <span
      className="inline-flex items-center gap-1 py-1"
      role="status"
      aria-label="Assistant is thinking"
    >
      <span className="h-2 w-2 animate-typing-bounce rounded-full bg-current [animation-delay:-0.3s]" />
      <span className="h-2 w-2 animate-typing-bounce rounded-full bg-current [animation-delay:-0.15s]" />
      <span className="h-2 w-2 animate-typing-bounce rounded-full bg-current" />
    </span>
  );
}
