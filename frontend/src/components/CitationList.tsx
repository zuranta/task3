import { Citation } from "../services/queries";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <ul aria-label="Citations">
      {citations.map((citation, index) => (
        <li key={`${citation.document_id}-${index}`}>
          {citation.document_filename} ({citation.location_label})
          {citation.source_removed && <em> — source document removed</em>}
        </li>
      ))}
    </ul>
  );
}
