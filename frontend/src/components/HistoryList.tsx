import { QueryRecord } from "../services/queries";

export function HistoryList({
  queries,
  onSelect,
}: {
  queries: QueryRecord[];
  onSelect: (queryId: string) => void;
}) {
  if (queries.length === 0) {
    return <p>You haven't asked any questions yet.</p>;
  }

  return (
    <ul aria-label="Query history">
      {queries.map((query) => (
        <li key={query.id}>
          <button type="button" onClick={() => onSelect(query.id)}>
            {query.question}
          </button>
          <span> — {query.status}</span>
        </li>
      ))}
    </ul>
  );
}
