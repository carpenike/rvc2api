import { render, screen } from "@testing-library/react";
import { Button } from "../components/Button";
import "@testing-library/jest-dom";

describe("Button component", () => {
  test("renders button with text", () => {
    render(<Button>Test Button</Button>);
    const buttonElement = screen.getByText("Test Button");
    expect(buttonElement).toBeInTheDocument();
  });

  test("applies variant classes correctly", () => {
    render(<Button variant="primary">Primary Button</Button>);
    const buttonElement = screen.getByText("Primary Button");
    expect(buttonElement).toHaveClass("bg-rv-primary");
  });

  test("invokes onClick handler when clicked", () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Clickable Button</Button>);

    const buttonElement = screen.getByText("Clickable Button");
    buttonElement.click();

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("disables the button when disabled prop is true", () => {
    render(<Button disabled>Disabled Button</Button>);
    const buttonElement = screen.getByText("Disabled Button");

    expect(buttonElement).toBeDisabled();
    expect(buttonElement).toHaveClass("opacity-50");
  });
});
