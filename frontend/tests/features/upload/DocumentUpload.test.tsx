import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../../src/features/auth/auth";
import { DocumentUpload } from "../../../src/features/upload/DocumentUpload";
import * as documentsApi from "../../../src/features/upload/documents";

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
  it("shows a loading indicator while the initial document list is pending", () => {
    vi.spyOn(documentsApi, "listDocuments").mockImplementation(() => new Promise(() => {}));

    render(<DocumentUpload />);

    expect(screen.getByLabelText(/loading your documents/i)).toBeInTheDocument();
  });

  it("shows a distinct empty-state message when there are no documents", async () => {
    vi.spyOn(documentsApi, "listDocuments").mockResolvedValue([]);

    render(<DocumentUpload />);

    expect(await screen.findByText(/no documents yet/i)).toBeInTheDocument();
  });

  it("shows a styled, human-readable error message when the document list fails to load", async () => {
    vi.spyOn(documentsApi, "listDocuments").mockRejectedValue(
      new ApiError("Could not load your documents.", 500),
    );

    render(<DocumentUpload />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Could not load your documents.");
    });
  });

  it("lists ready documents once loaded", async () => {
    vi.spyOn(documentsApi, "listDocuments").mockResolvedValue([
      {
        id: "doc-1",
        original_filename: "handbook.pdf",
        format: "pdf",
        status: "ready",
        failure_reason: null,
        uploaded_at: "2026-07-31T00:00:00.000Z",
      },
    ]);

    render(<DocumentUpload />);

    expect(await screen.findByText("handbook.pdf")).toBeInTheDocument();
    expect(screen.getByText("ready")).toBeInTheDocument();
  });

  it("makes a ready document clickable to view its passages, but not a still-processing one", async () => {
    vi.spyOn(documentsApi, "listDocuments").mockResolvedValue([
      {
        id: "doc-1",
        original_filename: "handbook.pdf",
        format: "pdf",
        status: "ready",
        failure_reason: null,
        uploaded_at: "2026-07-31T00:00:00.000Z",
      },
      {
        id: "doc-2",
        original_filename: "still-indexing.pdf",
        format: "pdf",
        status: "processing",
        failure_reason: null,
        uploaded_at: "2026-07-31T00:00:00.000Z",
      },
    ]);

    render(<DocumentUpload />);
    await screen.findByText("handbook.pdf");

    expect(
      screen.getByRole("button", { name: /view passages for handbook\.pdf/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /view passages for still-indexing\.pdf/i }),
    ).not.toBeInTheDocument();
  });

  it("uploads the selected file and shows it in the list once the refresh completes", async () => {
    const uploaded = {
      id: "doc-1",
      original_filename: "notes.txt",
      format: "txt" as const,
      status: "processing" as const,
      failure_reason: null,
      uploaded_at: "2026-07-31T00:00:00.000Z",
    };
    vi.spyOn(documentsApi, "listDocuments")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([uploaded]);
    const uploadSpy = vi.spyOn(documentsApi, "uploadDocument").mockResolvedValue(uploaded);

    const { container } = render(<DocumentUpload />);
    await screen.findByText(/no documents yet/i);

    await uploadAndSubmit(container, makeFile());

    await waitFor(() => expect(uploadSpy).toHaveBeenCalled());
    expect(await screen.findByText("notes.txt")).toBeInTheDocument();
  });

  it("shows the ApiError message when the upload is rejected", async () => {
    vi.spyOn(documentsApi, "listDocuments").mockResolvedValue([]);
    vi.spyOn(documentsApi, "uploadDocument").mockRejectedValue(
      new ApiError("The file is corrupted and could not be read.", 400),
    );

    const { container } = render(<DocumentUpload />);
    await screen.findByText(/no documents yet/i);
    await uploadAndSubmit(container, makeFile());

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The file is corrupted and could not be read.",
    );
  });

  it("shows a generic message for a non-ApiError upload failure", async () => {
    vi.spyOn(documentsApi, "listDocuments").mockResolvedValue([]);
    vi.spyOn(documentsApi, "uploadDocument").mockRejectedValue(new Error("network down"));

    const { container } = render(<DocumentUpload />);
    await screen.findByText(/no documents yet/i);
    await uploadAndSubmit(container, makeFile());

    expect(await screen.findByRole("alert")).toHaveTextContent("Upload failed. Please try again.");
  });
});
