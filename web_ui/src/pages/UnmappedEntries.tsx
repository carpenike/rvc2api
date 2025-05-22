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
    <div className="px-4 py-6 max-w-5xl mx-auto">
      <Card className="bg-[var(--color-bg)] border border-[var(--color-border)] shadow-md">
        <h1 className="text-2xl font-bold mb-4 text-[var(--color-text)]">Unmapped RV-C Entries</h1>
        <p className="mb-6 text-[var(--color-muted)]">
          The following entries were received on the RV-C network but could not be mapped to known DGNs or device types. This may indicate new, custom, or unsupported messages.
        </p>
        {error && (
          <div className="text-red-600 bg-red-50 border border-red-200 rounded p-4 my-4" role="alert">
            Error loading unmapped entries: {error}
          </div>
        )}
        {!loading && unmappedEntries.length === 0 && !error && (
          <div className="italic text-[var(--color-muted)]">No unmapped entries detected.</div>
        )}
        {!loading && unmappedEntries.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-y-1">
              <thead>
                <tr className="bg-[var(--color-bg-muted)]">
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">DGN</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">Source Address</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">Priority</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">Timestamp</th>
                  <th className="px-4 py-2 text-left font-semibold text-[var(--color-text)]">Data</th>
                </tr>
              </thead>
              <tbody>
                {unmappedEntries.map((entry, idx) => (
                  <tr key={entry.dgn ?? idx} className="hover:bg-[var(--color-primary)/10]">
                    <td className="px-4 py-2 font-mono text-[var(--color-text)]">
                      <Badge className="bg-[var(--color-primary)] text-white">{entry.dgn ?? "-"}</Badge>
                    </td>
                    <td className="px-4 py-2 text-[var(--color-text)]">{entry.source_address ?? "-"}</td>
                    <td className="px-4 py-2 text-[var(--color-text)]">{entry.priority ?? "-"}</td>
                    <td className="px-4 py-2 text-[var(--color-text)]">{entry.timestamp ? new Date(entry.timestamp).toLocaleString() : "-"}</td>
                    <td className="px-4 py-2 text-[var(--color-text)]">
                      {Array.isArray(entry.data) && entry.data.length > 0
                        ? entry.data.map((b) => b.toString(16).padStart(2, "0")).join(" ")
                        : "-"}
                    </td>
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
