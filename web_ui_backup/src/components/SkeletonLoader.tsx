import { clsx } from "clsx";
import { memo } from "react";

interface SkeletonLoaderProps {
  /** Type of skeleton to render */
  variant?: "text" | "circular" | "rectangular" | "card";
  /** Width of the skeleton (CSS value) */
  width?: string | number;
  /** Height of the skeleton (CSS value) */
  height?: string | number;
  /** Additional CSS classes */
  className?: string;
  /** Number of lines for text variant */
  lines?: number;
}

/**
 * Skeleton loader component for showing loading states
 *
 * Provides different variants for different content types:
 * - text: For text content with multiple lines
 * - circular: For avatars or circular elements
 * - rectangular: For images or rectangular content
 * - card: For card-like components with title and content
 */
const SkeletonLoader = memo(function SkeletonLoader({
  variant = "rectangular",
  width,
  height,
  className,
  lines = 3
}: SkeletonLoaderProps) {
  const baseClasses = "animate-pulse bg-gray-200 dark:bg-gray-700";

  const getVariantClasses = () => {
    switch (variant) {
      case "text":
        return "rounded h-4";
      case "circular":
        return "rounded-full";
      case "rectangular":
        return "rounded";
      case "card":
        return "rounded-lg";
      default:
        return "rounded";
    }
  };

  const getStyle = () => ({
    width: typeof width === "number" ? `${width}px` : width,
    height: typeof height === "number" ? `${height}px` : height
  });

  if (variant === "text") {
    return (
      <div className={clsx("space-y-2", className)}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={clsx(
              baseClasses,
              getVariantClasses(),
              index === lines - 1 && "w-3/4" // Last line is shorter
            )}
            style={{
              width: index === lines - 1 ? "75%" : width,
              height: height || "1rem"
            }}
          />
        ))}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div className={clsx("p-4 border border-gray-200 dark:border-gray-700", getVariantClasses(), className)}>
        {/* Card title */}
        <div className={clsx(baseClasses, "rounded h-6 w-3/4 mb-3")} />
        {/* Card content lines */}
        <div className="space-y-2">
          <div className={clsx(baseClasses, "rounded h-4 w-full")} />
          <div className={clsx(baseClasses, "rounded h-4 w-5/6")} />
          <div className={clsx(baseClasses, "rounded h-4 w-4/5")} />
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(baseClasses, getVariantClasses(), className)}
      style={getStyle()}
    />
  );
});

export default SkeletonLoader;
