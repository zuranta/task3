import { ReactNode, useEffect, useState } from "react";

import { Alert, AlertDescription } from "../../components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { Skeleton } from "../../components/ui/skeleton";
import { ApiError } from "../auth/auth";
import { PassageSummary, getDocumentPassages } from "./documentPassages";

export function DocumentPassagesDialog({
  documentId,
  filename,
  trigger,
}: {
  documentId: string;
  filename: string;
  trigger: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [passages, setPassages] = useState<PassageSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setPassages(null);
    setError(null);
    getDocumentPassages(documentId)
      .then(setPassages)
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Could not load this document's passages.",
        );
      });
  }, [open, documentId]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="truncate">{filename}</DialogTitle>
          <DialogDescription>The passages this document was indexed as.</DialogDescription>
        </DialogHeader>

        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : passages === null ? (
          <div className="space-y-2" aria-label="Loading passages">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : passages.length === 0 ? (
          <p className="text-sm text-muted-foreground">No passages were found for this document.</p>
        ) : (
          <ul aria-label="Passages" className="space-y-4">
            {passages.map((passage, index) => (
              <li key={index}>
                <p className="text-xs font-medium text-muted-foreground">
                  {passage.location_label}
                </p>
                <p className="whitespace-pre-wrap break-words text-sm">{passage.content}</p>
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
}
