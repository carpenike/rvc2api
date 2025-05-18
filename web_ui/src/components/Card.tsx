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
}

/**
 * Card component
 *
 * A container component with consistent styling used throughout the application
 * for grouping related content.
 *
 * @param props - Component properties
 * @returns A styled card component
 */
export function Card({ title, children, className = "" }: CardProps) {
  return (
    <div className={`card ${className}`}>
      {title && <h2 className="text-xl font-semibold mb-4">{title}</h2>}
      <div>{children}</div>
    </div>
  );
}
