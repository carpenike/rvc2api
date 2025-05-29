import { render, screen } from "@testing-library/react";
import LoadingSpinner from "../LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders the spinner without a label", () => {
    render(<LoadingSpinner />);

    // Check for the SVG spinner
    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass("animate-spin");
  });

  it("renders the spinner with a label", () => {
    render(<LoadingSpinner label="Loading data..." />);

    // Check for the SVG spinner
    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toBeInTheDocument();

    // Check for the label
    expect(screen.getByText("Loading data...")).toBeInTheDocument();
  });

  it("does not render label when not provided", () => {
    render(<LoadingSpinner />);

    // Should not have any text content
    const container = screen.getByRole("img", { hidden: true }).closest("div");
    const textElement = container?.querySelector("span");
    expect(textElement).not.toBeInTheDocument();
  });

  it("applies correct CSS classes", () => {
    render(<LoadingSpinner label="Test" />);

    const container = screen.getByRole("img", { hidden: true }).closest("div");
    expect(container).toHaveClass("flex", "flex-col", "items-center", "justify-center", "h-full", "p-8");

    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toHaveClass("animate-spin", "h-8", "w-8", "text-blue-500", "mb-2");

    const label = screen.getByText("Test");
    expect(label).toHaveClass("text-sm", "text-gray-600");
  });

  it("renders with proper structure", () => {
    render(<LoadingSpinner label="Loading..." />);

    const container = screen.getByRole("img", { hidden: true }).closest("div");
    expect(container).toBeInTheDocument();

    // Check SVG structure
    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner.tagName).toBe("svg");
    expect(spinner).toHaveAttribute("viewBox", "0 0 24 24");

    // Check for circle and path elements
    const circle = spinner.querySelector("circle");
    const path = spinner.querySelector("path");
    expect(circle).toBeInTheDocument();
    expect(path).toBeInTheDocument();
  });
});
