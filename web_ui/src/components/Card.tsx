import clsx from "clsx";
import type { ReactNode } from "react";

/**
 * Card component props
 */
interface CardProps {
  /** Card title - can be a string or React element */
  title?: ReactNode;

  /** Card content */
  children: ReactNode;

  /** Additional CSS classes to apply */
  className?: string;

  /** Optional aria-label for the card region */
  ariaLabel?: string;
}

/**
 * Card component for displaying content in a styled, theme-adaptive container.
 *
 * - Uses semantic Tailwind tokens for theme adaptation
 * - Accessible: uses <section> with optional aria-label, semantic heading
 * - Robust className merging
 *
 * @param {object} props - Component properties
 * @param {ReactNode} [props.title] - Card title (string or React element)
 * @param {ReactNode} props.children - Card content
 * @param {string} [props.className] - Additional CSS classes to apply
 * @param {string} [props.ariaLabel] - Optional aria-label for the card region
 * @returns {JSX.Element} A styled, accessible, theme-adaptive card component
 */
export function Card(props: CardProps) {
  const { title, children, className = "", ariaLabel } = props;
  return (
    <section
      className={clsx(
        // Theme-adaptive, semantic tokens
        "rounded-lg shadow-md border border-rv-border bg-rv-surface text-rv-text p-6",
        "transition-colors duration-200",
        className
      )}
      aria-label={ariaLabel}
      role="region"
      data-testid="card"
    >
      {title && (
        <h2 className="text-lg font-semibold mb-4 text-rv-heading" tabIndex={-1} id={typeof title === "string" ? `card-title-${title.replace(/\s+/g, "-").toLowerCase()}` : undefined}>
          {title}
        </h2>
      )}
      <div>{children}</div>
    </section>
  );
}
