import { useCallback, useEffect, useRef, useState } from "react";

interface UseAutoScrollOptions {
  enabled: boolean;
  threshold?: number;
  smoothBehavior?: boolean;
}

export function useAutoScroll({
  enabled,
  threshold = 100,
  smoothBehavior = true,
}: UseAutoScrollOptions) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Check if user is near bottom of container
  const checkIfAtBottom = useCallback(() => {
    const container = containerRef.current;
    if (!container) return false;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    return distanceFromBottom <= threshold;
  }, [threshold]);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    setIsUserScrolling(true);
    setIsAtBottom(checkIfAtBottom());

    // Clear previous timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // Set user scrolling to false after inactivity
    scrollTimeoutRef.current = setTimeout(() => {
      setIsUserScrolling(false);
    }, 150);
  }, [checkIfAtBottom]);

  // Auto-scroll to bottom when new content is added
  const scrollToBottom = useCallback(() => {
    const container = containerRef.current;
    if (!container || !enabled) return;

    // Only auto-scroll if user isn't manually scrolling and is near bottom
    if (!isUserScrolling && isAtBottom) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: smoothBehavior ? "smooth" : "auto",
      });
    }
  }, [enabled, isUserScrolling, isAtBottom, smoothBehavior]);

  // Force scroll to bottom (user action)
  const forceScrollToBottom = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    container.scrollTo({
      top: container.scrollHeight,
      behavior: smoothBehavior ? "smooth" : "auto",
    });
    setIsAtBottom(true);
  }, [smoothBehavior]);

  // Setup scroll listener
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      container.removeEventListener("scroll", handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  return {
    containerRef,
    isAtBottom,
    isUserScrolling,
    scrollToBottom,
    forceScrollToBottom,
  };
}
