import { useEffect, useState } from "react";
import { fetchDeviceMappings } from "../api/endpoints";
import type { DeviceMapping } from "../api/types";
import { Card, Loading } from "../components";
import { timeAgo } from "../utils/date";

/**
 * Device Mapping page component
 *
 * Displays a list of all RV-C devices on the network with their source addresses,
 * names, manufacturers, and last seen timestamps. Provides filtering and sorting capabilities.
 *
 * @returns The DeviceMapping page component
 */
export function DeviceMapping() {
  /** List of device mappings from the API */
  const [devices, setDevices] = useState<DeviceMapping[]>([]);

  /** Loading state for the API call */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

  /** Filter text for searching devices */
  const [filter, setFilter] = useState("");

  /** Current property to sort the device list by */
  const [sortBy, setSortBy] = useState<keyof DeviceMapping>("source_address");

  /** Current sort direction (ascending or descending) */
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  useEffect(() => {
    /**
     * Loads device mapping data from the API
     */
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchDeviceMappings();
        setDevices(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }

    void loadData();

    // Refresh every minute
    const interval = setInterval(() => {
      void loadData();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Filter and sort devices
  const filteredDevices = devices
    .filter((d) => {
      const search = filter.toLowerCase();
      return (
        d.name?.toLowerCase().includes(search) ||
        d.manufacturer?.toLowerCase().includes(search) ||
        d.device_type?.toLowerCase().includes(search) ||
        String(d.source_address).includes(search)
      );
    })
    .sort((a, b) => {
      const aVal = a[sortBy] ?? "";
      const bVal = b[sortBy] ?? "";
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });

  // Helper for rendering sort indicator
  function renderSortIndicator(col: keyof DeviceMapping) {
    if (sortBy !== col) return null;
    return (
      <span className="ml-1 text-xs align-middle">{sortDir === "asc" ? "▲" : "▼"}</span>
    );
  }

  // Handler for sorting by column
  function handleSort(col: keyof DeviceMapping) {
    if (sortBy === col) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setSortDir("asc");
    }
  }

  return (
    <main className="min-h-screen bg-background text-foreground p-4 md:p-8">
      <h1 className="text-2xl md:text-3xl font-bold mb-6 text-primary">Device Mapping</h1>
      <Card className="mb-6 bg-card text-card-foreground">
        <div className="flex flex-col md:flex-row md:items-center gap-4 mb-2">
          <label htmlFor="filter" className="text-sm font-medium text-muted-foreground">
            Filter
          </label>
          <input
            id="filter"
            type="text"
            className="bg-background text-foreground border border-border placeholder:text-muted-foreground rounded-md shadow-sm px-3 py-2 w-full md:w-64 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 transition-colors"
            placeholder="Name, manufacturer, address, ..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            aria-label="Filter devices"
            autoComplete="off"
          />
          <label htmlFor="sort-by" className="text-sm font-medium text-muted-foreground md:ml-4">
            Sort by
          </label>
          <select
            id="sort-by"
            className="bg-background text-foreground border border-border rounded-md shadow-sm px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 w-full md:w-48 transition-colors"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as keyof DeviceMapping)}
            aria-label="Sort devices by property"
          >
            <option value="source_address">Source Address</option>
            <option value="name">Name</option>
            <option value="manufacturer">Manufacturer</option>
            <option value="device_type">Type</option>
            <option value="last_seen">Last Seen</option>
          </select>
          <button
            className="ml-2 px-2 py-1 rounded bg-muted text-foreground border border-border hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label={`Sort ${sortDir === "asc" ? "descending" : "ascending"}`}
            onClick={() => setSortDir(sortDir === "asc" ? "desc" : "asc")}
            type="button"
          >
            {sortDir === "asc" ? "▲" : "▼"}
          </button>
        </div>
      </Card>
      <Card className="bg-card text-card-foreground">
        {error ? (
          <div
            role="alert"
            aria-live="assertive"
            className="my-8 bg-error/10 border border-error text-error rounded-md px-4 py-3 text-sm font-medium flex items-center gap-2 justify-center"
            data-testid="device-mapping-error"
          >
            <span className="material-symbols-outlined text-error" aria-hidden="true">error</span>
            {error === "{\"detail\":\"Not Found\"}" || error.includes("Not Found")
              ? "No device mapping data found. Please check your backend connection or try again later."
              : error}
          </div>
        ) : (
          <>
            {loading ? (
              <Loading aria-label="Loading device mappings" />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full border border-border rounded-lg bg-background text-foreground text-sm">
                  <caption className="sr-only">Device mapping table</caption>
                  <thead className="bg-muted text-muted-foreground">
                    <tr>
                      <th className="px-4 py-2 text-left cursor-pointer select-none" onClick={() => handleSort("source_address")}>Address{renderSortIndicator("source_address")}</th>
                      <th className="px-4 py-2 text-left cursor-pointer select-none" onClick={() => handleSort("name")}>Name{renderSortIndicator("name")}</th>
                      <th className="px-4 py-2 text-left cursor-pointer select-none" onClick={() => handleSort("device_type")}>Type{renderSortIndicator("device_type")}</th>
                      <th className="px-4 py-2 text-left cursor-pointer select-none" onClick={() => handleSort("manufacturer")}>Manufacturer{renderSortIndicator("manufacturer")}</th>
                      <th className="px-4 py-2 text-left cursor-pointer select-none" onClick={() => handleSort("last_seen")}>Last Seen{renderSortIndicator("last_seen")}</th>
                      <th className="px-4 py-2 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDevices.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center py-4 text-muted-foreground">
                          No devices found.
                        </td>
                      </tr>
                    ) : (
                      filteredDevices.map((d) => (
                        <tr key={d.source_address} className="even:bg-muted/50">
                          <td className="px-4 py-2 font-mono">{d.source_address}</td>
                          <td className="px-4 py-2">{d.name || <span className="italic text-muted-foreground">Unknown</span>}</td>
                          <td className="px-4 py-2">{d.device_type || <span className="italic text-muted-foreground">Unknown</span>}</td>
                          <td className="px-4 py-2">{d.manufacturer || <span className="italic text-muted-foreground">Unknown</span>}</td>
                          <td className="px-4 py-2">{d.last_seen ? timeAgo(d.last_seen) : <span className="italic text-muted-foreground">Never</span>}</td>
                          <td className="px-4 py-2">
                            {d.status === "active" ? (
                              <span className="inline-block px-2 py-0.5 rounded bg-success/20 text-success">Active</span>
                            ) : (
                              <span className="inline-block px-2 py-0.5 rounded bg-muted text-muted-foreground">Inactive</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </Card>
    </main>
  );
}
