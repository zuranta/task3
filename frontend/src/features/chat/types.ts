import { Citation } from "../query/queries";

/**
 * Client-side view model for one turn in the chat conversation. This is
 * ephemeral, session-only state — a rendering projection of the
 * Query/Answer/Citation records the backend already persists (see
 * data-model.md's "Frontend View Models" section) - not a new
 * server-side entity.
 */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp: string;
  status: "pending" | "complete" | "error";
}
