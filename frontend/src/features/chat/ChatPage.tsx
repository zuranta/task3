import { BarChart3, ClipboardList, History, LogOut } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "../../components/ui/button";
import { useAuth } from "../auth/auth";
import { DocumentUpload } from "../upload/DocumentUpload";
import { ChatInput } from "./ChatInput";
import { ChatWindow } from "./ChatWindow";
import { useConversation } from "./useConversation";

export function ChatPage() {
  const { logout, isAdmin } = useAuth();
  const { messages, sendQuestion, isPending } = useConversation();

  return (
    <div className="flex h-screen flex-col bg-muted/40">
      <header className="flex shrink-0 items-center justify-between border-b border-border bg-background px-4 py-3">
        <h1 className="text-lg font-semibold">RAG Document Q&amp;A</h1>
        <nav className="flex items-center gap-1">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/history">
              <History className="h-4 w-4" />
              History
            </Link>
          </Button>
          {isAdmin && (
            <Button variant="ghost" size="sm" asChild>
              <Link to="/admin/eval">
                <ClipboardList className="h-4 w-4" />
                Evaluation
              </Link>
            </Button>
          )}
          {isAdmin && (
            <Button variant="ghost" size="sm" asChild>
              <Link to="/admin/metrics">
                <BarChart3 className="h-4 w-4" />
                Metrics
              </Link>
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </nav>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4 lg:flex-row lg:overflow-hidden">
        <aside className="shrink-0 lg:w-80 lg:overflow-y-auto">
          <DocumentUpload />
        </aside>

        <main className="flex min-h-[60vh] flex-1 flex-col rounded-lg border border-border bg-background lg:min-h-0">
          <ChatWindow messages={messages} />
          <ChatInput onAsk={sendQuestion} isAsking={isPending} />
        </main>
      </div>
    </div>
  );
}
