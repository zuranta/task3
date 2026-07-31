import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../../src/features/auth/auth";
import { DocumentPassagesDialog } from "../../../src/features/upload/DocumentPassagesDialog";
import * as documentPassagesApi from "../../../src/features/upload/documentPassages";

function renderDialog() {
  return render(
    <DocumentPassagesDialog
      documentId="doc-1"
      filename="handbook.md"
      trigger={<button type="button">View passages for handbook.md</button>}
    />,
  );
}

describe("DocumentPassagesDialog", () => {
  it("fetches and shows a loading indicator only after the trigger is clicked", async () => {
    const user = userEvent.setup();
    const getSpy = vi
      .spyOn(documentPassagesApi, "getDocumentPassages")
      .mockImplementation(() => new Promise(() => {}));

    renderDialog();
    expect(getSpy).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: /view passages for handbook\.md/i }));

    expect(getSpy).toHaveBeenCalledWith("doc-1");
    expect(screen.getByLabelText(/loading passages/i)).toBeInTheDocument();
  });

  it("shows the document's passages once loaded", async () => {
    const user = userEvent.setup();
    vi.spyOn(documentPassagesApi, "getDocumentPassages").mockResolvedValue([
      { location_label: "Section 1 of 2", content: "First passage content." },
      { location_label: "Section 2 of 2", content: "Second passage content." },
    ]);

    renderDialog();
    await user.click(screen.getByRole("button", { name: /view passages for handbook\.md/i }));

    expect(await screen.findByText("First passage content.")).toBeInTheDocument();
    expect(screen.getByText("Second passage content.")).toBeInTheDocument();
  });

  it("shows a distinct empty-state message when the document has no passages", async () => {
    const user = userEvent.setup();
    vi.spyOn(documentPassagesApi, "getDocumentPassages").mockResolvedValue([]);

    renderDialog();
    await user.click(screen.getByRole("button", { name: /view passages for handbook\.md/i }));

    expect(await screen.findByText(/no passages were found/i)).toBeInTheDocument();
  });

  it("shows a styled error message when the passages fail to load", async () => {
    const user = userEvent.setup();
    vi.spyOn(documentPassagesApi, "getDocumentPassages").mockRejectedValue(
      new ApiError("Document not found.", 404),
    );

    renderDialog();
    await user.click(screen.getByRole("button", { name: /view passages for handbook\.md/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Document not found.");
  });
});
