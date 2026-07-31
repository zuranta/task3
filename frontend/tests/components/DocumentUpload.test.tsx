import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DocumentUpload } from "../../src/components/DocumentUpload";
import { ApiError } from "../../src/services/auth";
import * as documentsService from "../../src/services/documents";

function makeFile(name = "notes.txt", content = "some content") {
  return new File([content], name, { type: "text/plain" });
}

// jsdom doesn't recalculate a file input's `required` validity after
// userEvent.upload() sets .files, so a real button click gets silently
// blocked by native constraint validation before the submit event ever
// fires. Dispatching the submit event directly bypasses that jsdom quirk,
// matching how a real browser behaves once the file is actually present.
async function uploadAndSubmit(container: HTMLElement, file: File) {
  const user = userEvent.setup();
  await user.upload(screen.getByLabelText(/upload a document/i), file);
  fireEvent.submit(container.querySelector("form")!);
}

describe("DocumentUpload", () => {
  it("uploads the selected file and calls onUploaded with the resulting document", async () => {
    const onUploaded = vi.fn();
    const uploaded = {
      id: "doc-1",
      original_filename: "notes.txt",
      format: "txt" as const,
      status: "processing" as const,
      failure_reason: null,
      uploaded_at: "2026-07-31T00:00:00Z",
    };
    vi.spyOn(documentsService, "uploadDocument").mockResolvedValue(uploaded);

    const { container } = render(<DocumentUpload onUploaded={onUploaded} />);
    await uploadAndSubmit(container, makeFile());

    await waitFor(() => {
      expect(onUploaded).toHaveBeenCalledWith(uploaded);
    });
  });

  it("shows the ApiError message when the upload is rejected", async () => {
    vi.spyOn(documentsService, "uploadDocument").mockRejectedValue(
      new ApiError("The file is corrupted and could not be read.", 400),
    );

    const { container } = render(<DocumentUpload onUploaded={vi.fn()} />);
    await uploadAndSubmit(container, makeFile());

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The file is corrupted and could not be read.",
    );
  });

  it("shows a generic message for a non-ApiError failure", async () => {
    vi.spyOn(documentsService, "uploadDocument").mockRejectedValue(new Error("network down"));

    const { container } = render(<DocumentUpload onUploaded={vi.fn()} />);
    await uploadAndSubmit(container, makeFile());

    expect(await screen.findByRole("alert")).toHaveTextContent("Upload failed. Please try again.");
  });
});
