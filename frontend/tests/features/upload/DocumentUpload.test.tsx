import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../../src/features/auth/auth";
import { DocumentUpload } from "../../../src/features/upload/DocumentUpload";
import * as documentsApi from "../../../src/features/upload/documents";

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
});
