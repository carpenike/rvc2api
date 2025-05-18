import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { DocSearch } from "../components/DocSearch";
import { fetchDocSearchStatus } from "../api/docsApi";

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
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">RV-C Documentation</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Search Documentation</h2>

            {isSearchAvailable === false && (
              <div className="bg-amber-50 border-l-4 border-amber-500 p-4 mb-4">
                <h3 className="font-medium text-amber-700">Search Not Available</h3>
                <p className="text-amber-700 mt-1">
                  {searchStatus?.vector_search?.error ? (
                    <>
                      Error: {searchStatus.vector_search.error}
                      <br /><br />
                    </>
                  ) : null}
                  The documentation search feature requires setup. Please run:
                  <br />
                  <code className="bg-gray-100 px-1 py-0.5 rounded">python scripts/setup_faiss.py --setup</code>
                </p>
              </div>
            )}

            {isSearchAvailable === true && (
              <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4">
                <h3 className="font-medium text-green-700">Search Ready</h3>
                <p className="text-green-700 mt-1">
                  Documentation search is operational using
                  {searchStatus?.vector_search?.embedding_model && (
                    <> the <code className="bg-gray-100 px-1 py-0.5 rounded">{searchStatus.vector_search.embedding_model}</code> model</>
                  )}
                </p>
              </div>
            )}

            <DocSearch />
          </div>

          <div className="bg-white p-4 rounded-lg shadow mt-6">
            <h2 className="text-xl font-semibold mb-4">Documentation Resources</h2>
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
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">About RV-C Documentation Search</h2>

            <p className="mb-4">
              This feature uses AI-powered semantic search to help you find relevant information
              in the RV-C specification. The search goes beyond simple keyword matching to understand
              the meaning behind your query.
            </p>

            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
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

            <div className="mt-6 bg-gray-50 p-4 rounded border border-gray-200">
              <h3 className="font-medium mb-2">Administrator Setup</h3>
              <p className="text-sm text-gray-600">
                If the search functionality isn't working, administrators need to:
              </p>
              <ol className="list-decimal pl-5 text-sm text-gray-600 mt-1">
                <li>Place the RV-C specification PDF in the resources directory</li>
                <li>Configure an OpenAI API key for embeddings generation</li>
                <li>Run the setup script: <code>python scripts/setup_faiss.py --setup</code></li>
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
