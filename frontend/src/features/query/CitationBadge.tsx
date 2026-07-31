import { AlertTriangle, FileText } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { Citation } from "./queries";

/**
 * Shared citation rendering used by both the chat conversation (ChatBubble)
 * and the History detail view, so a citation always looks the same
 * regardless of where it's shown (FR-029/FR-031, research.md §14). Clicking
 * it opens the exact passage the answer was grounded in -- snapshotted on
 * the Citation itself at answer time, so no fetch is needed here.
 */
export function CitationBadge({ citation }: { citation: Citation }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          aria-label={`View source passage for ${citation.document_filename}`}
        >
          <Badge
            variant="citation"
            className="cursor-pointer gap-1 font-normal hover:bg-citation/80"
          >
            {citation.source_removed ? (
              <AlertTriangle className="h-3 w-3" />
            ) : (
              <FileText className="h-3 w-3" />
            )}
            <span>
              {citation.document_filename} ({citation.location_label})
              {citation.source_removed && " — source removed"}
            </span>
          </Badge>
        </button>
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="truncate">{citation.document_filename}</DialogTitle>
          <DialogDescription>
            {citation.location_label}
            {citation.source_removed && " — this source document has since been removed"}
          </DialogDescription>
        </DialogHeader>
        <p className="whitespace-pre-wrap break-words text-sm">{citation.passage_content}</p>
      </DialogContent>
    </Dialog>
  );
}

function dedupeCitations(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  return citations.filter((citation) => {
    const key = `${citation.document_id}::${citation.location_label}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function CitationBadgeList({ citations }: { citations: Citation[] }) {
  const uniqueCitations = dedupeCitations(citations);
  if (uniqueCitations.length === 0) return null;

  return (
    <ul aria-label="Citations" className="mt-2 flex flex-wrap gap-1.5">
      {uniqueCitations.map((citation) => (
        <li key={`${citation.document_id}-${citation.location_label}`}>
          <CitationBadge citation={citation} />
        </li>
      ))}
    </ul>
  );
}
