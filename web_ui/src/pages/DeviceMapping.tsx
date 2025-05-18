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

  /**
   * Handles sorting of device list when a column header is clicked
   *
   * @param key - The DeviceMapping property to sort by
   */
  const handleSort = (key: keyof DeviceMapping) => {
    if (sortBy === key) {
      // If already sorting by this key, toggle direction
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      // Otherwise, sort by the new key in ascending order
      setSortBy(key);
      setSortDir("asc");
    }
  };

  // Filter and sort devices
  const filteredDevices = devices
    .filter((device) => {
      if (!filter) return true;
      const searchTerm = filter.toLowerCase();
      return (
        String(device.source_address).includes(searchTerm) ||
        (device.name?.toLowerCase().includes(searchTerm) ?? false) ||
        (device.device_type?.toLowerCase().includes(searchTerm) ?? false) ||
        (device.manufacturer?.toLowerCase().includes(searchTerm) ?? false)
      );
    })
    .sort((a, b) => {
      // Handle undefined values
      const aValue = a[sortBy] ?? "";
      const bValue = b[sortBy] ?? "";

      // Compare values based on sort direction
      if (sortDir === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  // Sort indicator component
  const SortIndicator = ({ column }: { column: keyof DeviceMapping }) => {
    if (sortBy !== column) return null;
    return <span className="ml-1">{sortDir === "asc" ? "▲" : "▼"}</span>;
  };

  if (loading && devices.length === 0) {
    return <Loading message="Loading device mappings..." />;
  }

  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">Device Mapping</h1>

      {error && (
        <div className="bg-rv-error/20 text-rv-error p-4 rounded-xl mb-6">
          Error loading device mappings: {error}
        </div>
      )}

      <div className="flex flex-col md:flex-row justify-between gap-4 mb-6">
        <div className="relative w-full md:w-64">
          <input
            type="text"
            placeholder="Filter devices..."
            className="w-full p-2 pl-8 bg-rv-surface text-rv-text rounded-lg focus:ring-2 focus:ring-rv-primary border border-rv-surface/60 focus:outline-none"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <svg
            className="absolute left-2 top-2.5 h-4 w-4 text-rv-text/50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <div className="flex items-center">
          <span className="text-rv-text/70 mr-2">Showing:</span>
          <span className="bg-rv-primary/20 text-rv-primary px-3 py-1 rounded-lg">
            {filteredDevices.length} of {devices.length} devices
          </span>
        </div>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-rv-surface/60 text-left">
              <tr>
                <th
                  className="p-3 cursor-pointer"
                  onClick={() => handleSort("source_address")}
                >
                  Address <SortIndicator column="source_address" />
                </th>
                <th
                  className="p-3 cursor-pointer"
                  onClick={() => handleSort("name")}
                >
                  Name <SortIndicator column="name" />
                </th>
                <th
                  className="p-3 cursor-pointer"
                  onClick={() => handleSort("device_type")}
                >
                  Type <SortIndicator column="device_type" />
                </th>
                <th
                  className="p-3 cursor-pointer"
                  onClick={() => handleSort("manufacturer")}
                >
                  Manufacturer <SortIndicator column="manufacturer" />
                </th>
                <th
                  className="p-3 cursor-pointer"
                  onClick={() => handleSort("status")}
                >
                  Status <SortIndicator column="status" />
                </th>
                <th
                  className="p-3 cursor-pointer"
                  onClick={() => handleSort("last_seen")}
                >
                  Last Seen <SortIndicator column="last_seen" />
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rv-surface/30">
              {filteredDevices.length > 0 ? (
                filteredDevices.map((device, index) => (
                  <tr key={index} className="hover:bg-rv-surface/20">
                    <td className="p-3">
                      <span className="font-mono bg-rv-surface/30 px-2 py-1 rounded">
                        {device.source_address}
                      </span>
                    </td>
                    <td className="p-3">{device.name || "—"}</td>
                    <td className="p-3">{device.device_type || "—"}</td>
                    <td className="p-3">{device.manufacturer || "—"}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          device.status === "active"
                            ? "bg-rv-success/20 text-rv-success"
                            : "bg-rv-error/20 text-rv-error"
                        }`}
                      >
                        {device.status || "unknown"}
                      </span>
                    </td>
                    <td className="p-3">
                      {device.last_seen ? timeAgo(device.last_seen) : "—"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-rv-text/60">
                    No devices match your filter criteria
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  );
}
