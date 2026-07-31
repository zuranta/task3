import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { CitationBadge, CitationBadgeList } from "../../../src/features/query/CitationBadge";
import { Citation } from "../../../src/features/query/queries";

function citation(overrides: Partial<Citation> = {}): Citation {
  return {
    document_id: "doc-1",
    document_filename: "handbook.md",
    location_label: "Section 1 of 1",
    source_removed: false,
    passage_content: "The handbook says refunds are available within 30 days.",
    ...overrides,
  };
}

describe("CitationBadgeList", () => {
  it("renders nothing for an empty citation list", () => {
    const { container } = render(<CitationBadgeList citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("collapses citations pointing at the same document and location into a single badge", () => {
    // Reproduces the model citing the same passage twice in its structured
    // output before the backend-side dedup fix landed - the frontend must
    // not show the same document/location twice either way.
    render(<CitationBadgeList citations={[citation(), citation()]} />);

    expect(screen.getAllByText(/handbook\.md/)).toHaveLength(1);
  });

  it("keeps citations to the same document at different locations as separate badges", () => {
    render(
      <CitationBadgeList
        citations={[
          citation({ location_label: "Section 1 of 2" }),
          citation({ location_label: "Section 2 of 2" }),
        ]}
      />,
    );

    expect(screen.getByText(/Section 1 of 2/)).toBeInTheDocument();
    expect(screen.getByText(/Section 2 of 2/)).toBeInTheDocument();
  });
});

describe("CitationBadge", () => {
  it("opens a dialog showing the cited passage's exact text when clicked", async () => {
    const user = userEvent.setup();
    render(<CitationBadge citation={citation()} />);

    expect(screen.queryByText(/The handbook says refunds/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /view source passage/i }));

    expect(await screen.findByText(/The handbook says refunds/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "handbook.md" })).toBeInTheDocument();
  });
});
