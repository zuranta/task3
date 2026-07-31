import { AlertTriangle, FileText } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Citation } from "./queries";

/**
 * Shared citation rendering used by both the chat conversation (ChatBubble)
 * and the History detail view, so a citation always looks the same
 * regardless of where it's shown (FR-029/FR-031, research.md §14).
 */
export function CitationBadge({ citation }: { citation: Citation }) {
  return (
    <Badge variant="citation" className="gap-1 font-normal">
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
  );
}

export function CitationBadgeList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <ul aria-label="Citations" className="mt-2 flex flex-wrap gap-1.5">
      {citations.map((citation, index) => (
        <li key={`${citation.document_id}-${index}`}>
          <CitationBadge citation={citation} />
        </li>
      ))}
    </ul>
  );
}
