import { useEffect, useState } from "react";
import { fetchUnmappedEntries } from "../api/endpoints";
import type { UnmappedEntry } from "../api/types";
import { Badge, Card, Loading } from "../components";

/**
 * Unmapped Entries page component
 *
 * Displays entries from the RV-C network that could not be properly
 * mapped to known DGNs or instances. This page helps identify potential
 * gaps in the RV-C protocol decoder implementation.
 *
 * @returns The UnmappedEntries page component
 */
export function UnmappedEntries() {
  /** List of unmapped entries from the API */
  const [unmappedEntries, setUnmappedEntries] = useState<UnmappedEntry[]>([]);

  /** Loading state for the API call */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    /**
     * Loads unmapped entries data from the API
     */
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchUnmappedEntries();
        setUnmappedEntries(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }

    void loadData();
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      void loadData();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && unmappedEntries.length === 0) {
    return <Loading message="Loading unmapped entries..." />;
  }

  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">Unmapped Entries</h1>

      {error && (
        <div className="bg-rv-error/20 text-rv-error p-4 rounded-xl mb-6">
          Error loading unmapped entries: {error}
        </div>
      )}

      <div className="mb-4 flex justify-between items-center">
        <div>
          <Badge>
            {unmappedEntries.length} unmapped{" "}
            {unmappedEntries.length === 1 ? "entry" : "entries"}
          </Badge>
        </div>
        <button
          className="px-4 py-2 bg-rv-primary/20 text-rv-primary hover:bg-rv-primary/30 rounded-lg"
          onClick={() => setUnmappedEntries([])}
        >
          Refresh
        </button>
      </div>

      {unmappedEntries.length > 0 ? (
        <div className="space-y-4">
          {unmappedEntries.map((entry, index) => (
            <Card key={index} title={`DGN: ${entry.dgn || "Unknown"}`}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-lg font-medium mb-2">Raw Data</h3>
                  <pre className="bg-rv-background/50 p-3 rounded-lg overflow-auto text-xs">
                    {JSON.stringify(entry.raw_data || entry, null, 2)}
                  </pre>
                </div>
                <div>
                  <h3 className="text-lg font-medium mb-2">Details</h3>
                  <dl className="grid grid-cols-3 gap-2 text-sm">
                    <dt className="text-rv-text/70">Source:</dt>
                    <dd className="col-span-2">
                      {entry.source_address || "Unknown"}
                    </dd>

                    <dt className="text-rv-text/70">Priority:</dt>
                    <dd className="col-span-2">
                      {entry.priority || "Unknown"}
                    </dd>

                    <dt className="text-rv-text/70">Timestamp:</dt>
                    <dd className="col-span-2">
                      {entry.timestamp || "Unknown"}
                    </dd>

                    <dt className="text-rv-text/70">Data Length:</dt>
                    <dd className="col-span-2">
                      {entry.data ? entry.data.length : "Unknown"} bytes
                    </dd>
                  </dl>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : !loading ? (
        <div className="bg-rv-surface p-8 rounded-xl text-center">
          <p className="text-xl">No unmapped entries found</p>
          <p className="text-rv-text/60 mt-2">
            All CAN messages have been successfully mapped to known entities.
          </p>
        </div>
      ) : null}
    </section>
  );
}
