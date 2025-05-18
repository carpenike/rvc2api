import { useEffect, useState } from "react";
import { fetchUnknownPgns } from "../api/endpoints";
import type { UnknownPgn } from "../api/types";
import { Badge, Card, Loading } from "../components";

/**
 * Unknown PGNs page component
 *
 * Displays a list of Parameter Group Numbers (PGNs) that have been
 * received on the RV-C network but are not recognized by the system.
 * Helps identify potential gaps in the RV-C protocol implementation.
 *
 * @returns The UnknownPgns page component
 */
export function UnknownPgns() {
  /** List of unknown PGNs from the API */
  const [unknownPgns, setUnknownPgns] = useState<UnknownPgn[]>([]);

  /** Loading state for the API call */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    /**
     * Loads unknown PGNs data from the API
     */
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchUnknownPgns();
        setUnknownPgns(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }

    void loadData();
    // Refresh data every minute
    const interval = setInterval(() => {
      void loadData();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading && unknownPgns.length === 0) {
    return <Loading message="Loading unknown PGNs..." />;
  }

  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">Unknown PGNs</h1>

      {error && (
        <div className="bg-rv-error/20 text-rv-error p-4 rounded-xl mb-6">
          Error loading unknown PGNs: {error}
        </div>
      )}

      <div className="mb-4 flex justify-between items-center">
        <div>
          <Badge>
            {unknownPgns.length} unknown{" "}
            {unknownPgns.length === 1 ? "PGN" : "PGNs"}
          </Badge>
        </div>
        <button
          className="px-4 py-2 bg-rv-primary/20 text-rv-primary hover:bg-rv-primary/30 rounded-lg"
          onClick={() => setUnknownPgns([])}
        >
          Refresh
        </button>
      </div>

      {unknownPgns.length > 0 ? (
        <div className="space-y-4">
          {unknownPgns.map((pgn, index) => (
            <Card key={index} title={`PGN: ${pgn.pgn || pgn.id || "Unknown"}`}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-lg font-medium mb-2">Occurrences</h3>
                  <div className="bg-rv-background/50 p-3 rounded-lg">
                    <div className="flex justify-between">
                      <span>First seen:</span>
                      <span>{pgn.first_seen || "Unknown"}</span>
                    </div>
                    <div className="flex justify-between mt-2">
                      <span>Last seen:</span>
                      <span>{pgn.last_seen || "Unknown"}</span>
                    </div>
                    <div className="flex justify-between mt-2">
                      <span>Count:</span>
                      <span>{pgn.occurrence_count || "Unknown"}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium mb-2">Sample Data</h3>
                  <pre className="bg-rv-background/50 p-3 rounded-lg overflow-auto text-xs h-32">
                    {JSON.stringify(pgn.sample_data || pgn, null, 2)}
                  </pre>
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium mb-2">Source Addresses</h3>
                <div className="flex flex-wrap gap-2">
                  {pgn.source_addresses ? (
                    pgn.source_addresses.map((src: number, i: number) => (
                      <Badge key={i} variant="secondary">
                        SA: {src}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-rv-text/60">
                      No source address data
                    </span>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : !loading ? (
        <div className="bg-rv-surface p-8 rounded-xl text-center">
          <p className="text-xl">No unknown PGNs found</p>
          <p className="text-rv-text/60 mt-2">
            All received PGNs are recognized by the system.
          </p>
        </div>
      ) : null}
    </section>
  );
}
