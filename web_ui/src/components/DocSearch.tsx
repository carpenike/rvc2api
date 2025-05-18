import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchDocumentation } from "../api/docsApi";
import type { SearchResult } from "../api/docsApi";

interface DocSearchProps {
  className?: string;
}

export function DocSearch({ className = "" }: DocSearchProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

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

    // Clear any existing timer
    const timerId = window.setTimeout(() => {
      setDebouncedQuery(e.target.value);
    }, 500);

    return () => window.clearTimeout(timerId);
  };

  return (
    <div className={`doc-search ${className}`}>
      <h3 className="text-lg font-medium mb-2">RV-C Documentation Search</h3>
      <div className="mb-4">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder="Search the RV-C documentation..."
          className="w-full px-4 py-2 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Search query"
        />
        {query.trim().length > 0 && query.trim().length < 3 && (
          <p className="text-sm text-gray-500 mt-1">Type at least 3 characters to search</p>
        )}
      </div>

      {isLoading && (
        <div className="flex justify-center items-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
          <span className="ml-2">Searching documentation...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error instanceof Error ? error.message : "Unknown error"}</span>
          {error instanceof Error && error.message.includes("not available") && (
            <div className="mt-2 text-sm">
              <p>To set up documentation search:</p>
              <ol className="list-decimal pl-5 mt-1">
                <li>Ensure the RV-C specification PDF is in the resources directory</li>
                <li>Set the OPENAI_API_KEY environment variable</li>
                <li>Run: <code className="bg-red-50 px-1">python scripts/setup_faiss.py --setup</code></li>
                <li>Restart the server</li>
              </ol>
            </div>
          )}
        </div>
      )}

      {!isLoading && !error && results.length === 0 && debouncedQuery.trim().length >= 3 && (
        <p className="text-gray-500">No documentation matches found for "{debouncedQuery}"</p>
      )}

      {results.length > 0 && (
        <div className="space-y-4 mt-2">
          <h4 className="text-md font-medium">Search Results</h4>
          {results.map((result: SearchResult, index: number) => (
            <div key={index} className="border rounded p-3 bg-white">
              <div className="font-medium text-blue-600">{result.section}: {result.title}</div>
              <div className="text-sm text-gray-500 mb-2">Pages: {result.pages.join(", ")}</div>
              <p className="text-gray-700 text-sm mt-1 line-clamp-3">
                {result.content.length > 300
                  ? `${result.content.substring(0, 300)}...`
                  : result.content}
              </p>
              <button
                className="mt-2 text-sm text-blue-500 hover:underline"
                onClick={() => window.alert("Full document viewer will be implemented in a future update.")}
              >
                View Full Section
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
