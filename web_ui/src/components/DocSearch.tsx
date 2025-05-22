import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
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
    <section
      className={clsx(
        "doc-search rounded-lg border border-rv-border bg-rv-surface text-rv-text p-6 shadow-sm transition-colors duration-200",
        className
      )}
      aria-label="Documentation Search"
      role="search"
      data-testid="doc-search"
    >
      <h2 className="text-lg font-semibold mb-2 text-rv-heading" id="doc-search-title">
        RV-C Documentation Search
      </h2>
      <div className="mb-4">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder="Search the RV-C documentation..."
          className="w-full px-4 py-2 rounded border border-rv-border bg-rv-surface text-rv-text focus:outline-none focus:ring-2 focus:ring-rv-primary"
          aria-label="Search query"
          aria-describedby="doc-search-help"
        />
        {query.trim().length > 0 && query.trim().length < 3 && (
          <p id="doc-search-help" className="text-sm text-rv-muted mt-1">
            Type at least 3 characters to search
          </p>
        )}
      </div>

      {isLoading && (
        <div className="flex justify-center items-center py-4" aria-live="polite">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-rv-primary"></div>
          <span className="ml-2 text-rv-muted">Searching documentation...</span>
        </div>
      )}

      {error && (
        <div className="text-rv-error bg-rv-error/10 rounded p-2 mt-2" role="alert">
          Error searching documentation. Please try again.
        </div>
      )}

      {!isLoading && !error && results.length === 0 && debouncedQuery.trim().length >= 3 && (
        <div className="text-rv-muted mt-2" role="status">
          No results found for "{debouncedQuery}".
        </div>
      )}

      {results.length > 0 && (
        <ul className="divide-y divide-rv-border mt-2" aria-label="Search results">
          {results.map((result: SearchResult, idx: number) => (
            <li key={result.section + "-" + result.pages.join("-") + "-" + idx} className="py-3">
              <a
                href={`#page-${result.pages[0]}`}
                className="text-rv-link hover:underline focus:underline focus:outline-none"
                tabIndex={0}
                aria-label={`Jump to documentation section: ${result.title}`}
              >
                <span className="font-medium text-rv-heading">{result.title}</span>
              </a>
              <span className="ml-2 text-xs text-rv-muted">(Section: {result.section}, Page{result.pages.length > 1 ? "s" : ""}: {result.pages.join(", ")})</span>
              {result.content && (
                <p className="text-sm text-rv-muted mt-1" style={{ wordBreak: "break-word" }}>
                  {result.content.length > 350 ? result.content.slice(0, 350) + "…" : result.content}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
