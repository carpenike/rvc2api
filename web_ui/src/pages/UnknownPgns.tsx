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
    <div className="px-4 py-6 max-w-5xl mx-auto">
      <Card className="bg-[var(--color-bg)] border border-[var(--color-border)] shadow-md">
        <h1 className="text-2xl font-bold mb-4 text-[var(--color-text)]">Unknown PGNs</h1>
        <p className="mb-6 text-[var(--color-muted)]">
          The following Parameter Group Numbers (PGNs) have been observed on the RV-C network but are not recognized by the system. This may indicate missing protocol support or new/undocumented messages.
        </p>
        {error && (
          <div className="text-red-600 bg-red-50 border border-red-200 rounded p-4 my-4" role="alert">
            Error loading unknown PGNs: {error}
          </div>
        )}
        {!loading && unknownPgns.length === 0 && !error && (
          <div className="italic text-[var(--color-muted)]">No unknown PGNs detected.</div>
        )}
        {!loading && unknownPgns.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-y-1">
              <thead>
                <tr className="bg-[var(--color-bg-muted)]">
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">PGN</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">Count</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">First Seen</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">Last Seen</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">Source Address</th>
                </tr>
              </thead>
              <tbody>
                {unknownPgns.map((pgn) => (
                  <tr key={pgn.pgn} className="hover:bg-[var(--color-primary)/10]">
                    <td className="px-4 py-2 font-mono text-[var(--color-text)]">
                      <Badge className="bg-[var(--color-primary)] text-white">{pgn.pgn}</Badge>
                    </td>
                    <td className="px-4 py-2 text-[var(--color-text)]">{pgn.occurrence_count ?? "-"}</td>
                    <td className="px-4 py-2 text-[var(--color-text)]">{pgn.first_seen ? new Date(pgn.first_seen).toLocaleString() : "-"}</td>
                    <td className="px-4 py-2 text-[var(--color-text)]">{pgn.last_seen ? new Date(pgn.last_seen).toLocaleString() : "-"}</td>
                    <td className="px-4 py-2 text-[var(--color-text)]">{Array.isArray(pgn.source_addresses) && pgn.source_addresses.length > 0 ? pgn.source_addresses.join(", ") : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
