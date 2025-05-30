import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import type { SearchResult } from "../api/docsApi";
import { searchDocumentation } from "../api/docsApi";

interface DocSearchProps {
  className?: string;
}

export function DocSearch({ className = "" }: DocSearchProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const debounceTimer = useRef<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: results = [], isLoading, error } = useQuery({
    queryKey: ["docSearch", debouncedQuery],
    queryFn: () => searchDocumentation(debouncedQuery),
    enabled: debouncedQuery.trim().length >= 3,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1 // Only retry once to avoid too many failed requests
  });

  // Debounce search input
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (debounceTimer.current) {
      window.clearTimeout(debounceTimer.current);
    }
    debounceTimer.current = window.setTimeout(() => {
      setDebouncedQuery(e.target.value);
    }, 500);
  };

  // Accessibility: focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <Card
      className={cn("doc-search", className)}
      aria-label="Documentation Search"
      role="search"
      data-testid="doc-search"
    >
      <CardHeader>
        <CardTitle id="doc-search-title">
          RV-C Documentation Search
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Search the RV-C documentation..."
            aria-label="Search query"
            aria-describedby="doc-search-help"
            className="w-full"
          />
          {query.trim().length > 0 && query.trim().length < 3 && (
            <p id="doc-search-help" className="text-sm text-muted-foreground">
              Type at least 3 characters to search
            </p>
          )}
        </div>

        {isLoading && (
          <div className="flex items-center space-x-2 py-4" aria-live="polite">
            <Skeleton className="h-4 w-4 rounded-full" />
            <span className="text-sm text-muted-foreground">Searching documentation...</span>
          </div>
        )}

        {error && (
          <Alert variant="destructive" role="alert">
            <AlertDescription>
              Error searching documentation. Please try again.
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && !error && results.length === 0 && debouncedQuery.trim().length >= 3 && (
          <div className="text-muted-foreground text-sm py-4" role="status">
            No results found for "{debouncedQuery}".
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-3" aria-label="Search results">
            {results.map((result: SearchResult, idx: number) => (
              <div key={result.section + "-" + result.pages.join("-") + "-" + idx} className="border-b border-border last:border-0 pb-3 last:pb-0">
                <a
                  href={`#page-${result.pages[0]}`}
                  className="text-primary hover:underline focus:underline focus:outline-none font-medium"
                  tabIndex={0}
                  aria-label={`Jump to documentation section: ${result.title}`}
                >
                  {result.title}
                </a>
                <div className="text-xs text-muted-foreground mt-1">
                  Section: {result.section}, Page{result.pages.length > 1 ? "s" : ""}: {result.pages.join(", ")}
                </div>
                {result.content && (
                  <p className="text-sm text-muted-foreground mt-2" style={{ wordBreak: "break-word" }}>
                    {result.content.length > 350 ? result.content.slice(0, 350) + "…" : result.content}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
