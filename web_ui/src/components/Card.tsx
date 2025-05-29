import {
  CardContent,
  CardHeader,
  CardTitle,
  Card as ShadcnCard
} from "@/components/ui/card";
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
    <ShadcnCard className={className} aria-label={ariaLabel} data-testid="card">
      {title && (
        <CardHeader>
          <CardTitle>
            {typeof title === "string" ? title : title}
          </CardTitle>
        </CardHeader>
      )}
      <CardContent>
        {children}
      </CardContent>
    </ShadcnCard>
  );
}
