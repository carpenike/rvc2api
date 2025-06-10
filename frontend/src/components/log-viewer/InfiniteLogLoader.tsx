import { useEffect, useRef } from "react";
import { useLogViewer } from "./useLogViewer";

export function InfiniteLogLoader() {
  const { fetchMore, hasMore, loading, mode } = useLogViewer();
  const loaderRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const currentLoader = loaderRef.current;
    if (!currentLoader) return;
    if (mode !== "history") return;
    const observer = new window.IntersectionObserver(
      (entries) => {
        const firstEntry = entries[0];
        if (firstEntry?.isIntersecting && hasMore && !loading) {
          void fetchMore();
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(currentLoader);
    return () => {
      observer.unobserve(currentLoader);
    };
  }, [loaderRef, fetchMore, hasMore, loading, mode]);

  if (mode !== "history") return null;
  return (
    <div ref={loaderRef} className="h-8 flex items-center justify-center text-xs text-muted-foreground">
      {hasMore ? (loading ? "Loading more..." : "Load more logs") : "End of logs"}
    </div>
  );
}
