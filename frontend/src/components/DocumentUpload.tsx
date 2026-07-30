import { FormEvent, useRef, useState } from "react";

import { ApiError } from "../services/auth";
import { DocumentRecord, uploadDocument } from "../services/documents";

export function DocumentUpload({ onUploaded }: { onUploaded: (document: DocumentRecord) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    setError(null);
    setIsUploading(true);
    try {
      const document = await uploadDocument(file);
      onUploaded(document);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} aria-label="Upload document">
      <label htmlFor="document-file">Upload a document (pdf, docx, txt, md)</label>
      <input id="document-file" type="file" ref={inputRef} accept=".pdf,.docx,.txt,.md" required />

      {error && <p role="alert">{error}</p>}

      <button type="submit" disabled={isUploading}>
        {isUploading ? "Uploading…" : "Upload"}
      </button>
    </form>
  );
}
