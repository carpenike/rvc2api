import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ModeToggle } from "./mode-toggle";

describe("ModeToggle", () => {
  it("renders the mode toggle button", () => {
    render(<ModeToggle />);

    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("has proper accessibility attributes", () => {
    render(<ModeToggle />);

    // Check for screen reader text
    expect(screen.getByText("Toggle theme")).toBeInTheDocument();
  });
});
