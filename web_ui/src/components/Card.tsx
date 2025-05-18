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
 * Card component for displaying content in a styled container.
 *
 * @param {object} props - Component properties
 * @param {ReactNode} [props.title] - Card title (string or React element)
 * @param {ReactNode} props.children - Card content
 * @param {string} [props.className] - Additional CSS classes to apply
 * @returns {JSX.Element} A styled card component
 */
export function Card(props: CardProps) {
  const { title, children, className = "" } = props;
  return (
    <div className={`card ${className}`}>
      {title && <h2 className="text-xl font-semibold mb-4">{title}</h2>}
      <div>{children}</div>
    </div>
  );
}
