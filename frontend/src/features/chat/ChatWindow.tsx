import { useEffect, useRef } from "react";

import { ChatBubble } from "./ChatBubble";
import { ChatMessage } from "./types";

export function ChatWindow({ messages }: { messages: ChatMessage[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-muted-foreground">
        Ask a question about your uploaded documents to start the conversation.
      </div>
    );
  }

  return (
    <div aria-label="Conversation" className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
      {messages.map((message) => (
        <ChatBubble key={message.id} message={message} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
