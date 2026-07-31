import { AlertTriangle, Bot, User } from "lucide-react";

import { Avatar, AvatarFallback } from "../../components/ui/avatar";
import { cn } from "../../lib/utils";
import { CitationBadgeList } from "../query/CitationBadge";
import { ChatMessage } from "./types";
import { TypingIndicator } from "./TypingIndicator";

export function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isError = message.status === "error";

  return (
    <div className={cn("flex items-start gap-2", isUser && "flex-row-reverse")}>
      <Avatar className="mt-0.5 shrink-0">
        <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : undefined}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          "min-w-0 max-w-[85%] rounded-lg px-3 py-2 text-sm sm:max-w-[75%]",
          isUser && "bg-primary text-primary-foreground",
          !isUser && !isError && "bg-card border border-border",
          isError && "border border-destructive/50 bg-destructive/10 text-destructive",
        )}
      >
        {message.status === "pending" ? (
          <TypingIndicator />
        ) : (
          <>
            {isError && (
              <div className="mb-1 flex items-center gap-1.5 font-medium">
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>Something went wrong</span>
              </div>
            )}
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
            {message.citations && message.citations.length > 0 && (
              <CitationBadgeList citations={message.citations} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
