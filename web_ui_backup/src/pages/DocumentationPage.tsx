import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { fetchDocSearchStatus } from "../api/docsApi";
import { DocSearch } from "../components/DocSearch";

export function DocumentationPage() {
  const [isSearchAvailable, setIsSearchAvailable] = useState<boolean | null>(null);

  // Query the search status API
  const { data: searchStatus, isError } = useQuery({
    queryKey: ["docSearchStatus"],
    queryFn: fetchDocSearchStatus,
    retry: 1,
    staleTime: 5 * 60 * 1000 // Cache for 5 minutes
  });

  // Update availability state when status changes
  useEffect(() => {
    if (searchStatus) {
      setIsSearchAvailable(searchStatus.vector_search.available);
    } else if (isError) {
      setIsSearchAvailable(false);
    }
  }, [searchStatus, isError]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6 text-primary">RV-C Documentation</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="bg-card text-card-foreground p-4 rounded-lg shadow border border-border">
            <h2 className="text-xl font-semibold mb-4 text-primary">Search Documentation</h2>

            {isSearchAvailable === false && (
              <div className="bg-warning/10 border-l-4 border-warning text-warning-foreground p-4 mb-4 rounded">
                <h3 className="font-medium">Search Not Available</h3>
                <p className="mt-1">
                  {searchStatus?.vector_search?.error ? (
                    <>
                      Error: {searchStatus.vector_search.error}
                      <br /><br />
                    </>
                  ) : null}
                  The documentation search feature requires setup. Please run:
                  <br />
                  <code className="bg-muted text-muted-foreground px-1 py-0.5 rounded">poetry run python scripts/setup_faiss.py --setup</code>
                </p>
              </div>
            )}

            {isSearchAvailable === true && (
              <div className="bg-success/10 border-l-4 border-success text-success-foreground p-4 mb-4 rounded">
                <h3 className="font-medium">Search Ready</h3>
                <p className="mt-1">You can now search the documentation using the box below.</p>
              </div>
            )}

            <DocSearch />
          </div>

          <div className="bg-card text-card-foreground p-4 rounded-lg shadow border border-border mt-6">
            <h2 className="text-xl font-semibold mb-4 text-primary">Documentation Resources</h2>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://www.rv-c.com/?q=node/75"
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Official RV-C Website
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/carpenike/rvc2api/blob/main/docs/rv-c-documentation-search.md"
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Setting Up RV-C Documentation Search
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="md:col-span-2">
          <div className="bg-card text-card-foreground p-6 rounded-lg shadow border border-border">
            <h2 className="text-xl font-semibold mb-4 text-primary">About RV-C Documentation Search</h2>

            <p className="mb-4">
              This feature uses AI-powered semantic search to help you find relevant information
              in the RV-C specification. The search goes beyond simple keyword matching to understand
              the meaning behind your query.
            </p>

            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 rounded">
              <h3 className="font-medium text-blue-700">How It Works</h3>
              <p className="text-blue-700 mt-1">
                Your search query is converted into a vector embedding using OpenAI's models, then
                compared with pre-embedded sections of the RV-C specification to find the most
                semantically similar content.
              </p>
            </div>

            <h3 className="font-medium mb-2 mt-6">Search Tips</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>Use natural language questions: "How does battery charging work?"</li>
              <li>Include specific terms when looking for technical details</li>
              <li>Try different phrasings if you don't get useful results</li>
              <li>Be specific about what you're looking for</li>
            </ul>

            <div className="mt-6 bg-muted text-muted-foreground p-4 rounded border border-border">
              <h3 className="font-medium mb-2">Administrator Setup</h3>
              <p className="text-sm">
                If the search functionality isn't working, administrators need to:
              </p>
              <ol className="list-decimal pl-5 text-sm mt-1">
                <li>Place the RV-C specification PDF in the resources directory</li>
                <li>Configure an OpenAI API key for embeddings generation</li>
                <li>Run the setup script: <code>poetry run python scripts/setup_faiss.py --setup</code></li>
                <li>Restart the server</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DocumentationPage;
