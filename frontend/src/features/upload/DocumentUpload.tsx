import { FileText, Loader2, Trash2, UploadCloud } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";

import { Alert, AlertDescription } from "../../components/ui/alert";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Skeleton } from "../../components/ui/skeleton";
import { ApiError } from "../auth/auth";
import { DocumentPassagesDialog } from "./DocumentPassagesDialog";
import { DocumentRecord, deleteDocument, listDocuments, uploadDocument } from "./documents";

const STATUS_VARIANT: Record<DocumentRecord["status"], "secondary" | "default" | "destructive"> = {
  processing: "secondary",
  ready: "default",
  failed: "destructive",
  deleted: "secondary",
};

export function DocumentUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void refreshDocuments();
  }, []);

  async function refreshDocuments() {
    try {
      setDocuments(await listDocuments());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load your documents.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    setError(null);
    setIsUploading(true);
    try {
      await uploadDocument(file);
      if (inputRef.current) inputRef.current.value = "";
      await refreshDocuments();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(documentId: string) {
    setError(null);
    try {
      await deleteDocument(documentId);
      await refreshDocuments();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the document.");
    }
  }

  const visibleDocuments = documents.filter((doc) => doc.status !== "deleted");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Your documents</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          onSubmit={handleSubmit}
          aria-label="Upload document"
          className="flex flex-col gap-2 sm:flex-row sm:items-center"
        >
          <div className="flex-1">
            <Label htmlFor="document-file" className="sr-only">
              Upload a document (pdf, docx, txt, md)
            </Label>
            <Input
              id="document-file"
              type="file"
              ref={inputRef}
              accept=".pdf,.docx,.txt,.md"
              required
            />
          </div>
          <Button type="submit" disabled={isUploading}>
            {isUploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <UploadCloud className="h-4 w-4" />
            )}
            {isUploading ? "Uploading…" : "Upload"}
          </Button>
        </form>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isLoading ? (
          <div className="space-y-2" aria-label="Loading your documents">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : visibleDocuments.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No documents yet. Upload one above to start asking questions about it.
          </p>
        ) : (
          <ul
            aria-label="Your documents"
            className="divide-y divide-border rounded-md border border-border"
          >
            {visibleDocuments.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between gap-2 p-3">
                {doc.status === "ready" ? (
                  <DocumentPassagesDialog
                    documentId={doc.id}
                    filename={doc.original_filename}
                    trigger={
                      <button
                        type="button"
                        className="flex min-w-0 items-center gap-2 rounded-sm text-left hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        aria-label={`View passages for ${doc.original_filename}`}
                      >
                        <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="min-w-0 truncate text-sm font-medium">
                          {doc.original_filename}
                        </span>
                      </button>
                    }
                  />
                ) : (
                  <div className="flex min-w-0 items-center gap-2">
                    <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{doc.original_filename}</p>
                      {doc.failure_reason && (
                        <p className="truncate text-xs text-destructive">{doc.failure_reason}</p>
                      )}
                    </div>
                  </div>
                )}
                <div className="flex shrink-0 items-center gap-2">
                  <Badge variant={STATUS_VARIANT[doc.status]}>{doc.status}</Badge>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete ${doc.original_filename}`}
                    onClick={() => handleDelete(doc.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
