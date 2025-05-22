import { useEffect, useState } from "react";
import { fetchRvcSpec } from "../api/endpoints";
import type { RvcSpecData } from "../api/types";
import { Card, Loading } from "../components";

/**
 * RV-C Specification page component
 *
 * Displays detailed information about the RV-C protocol specification,
 * including DGNs, messages, data types, and instances. Provides
 * navigation between different sections of the specification.
 *
 * @returns The RvcSpec page component
 */
export function RvcSpec() {
  // RV-C specification data from the API
  const [_specData, setSpecData] = useState<RvcSpecData | null>(null);
  // Loading state for the API call
  const [loading, setLoading] = useState(false);
  // Error state for failed API calls
  const [error, setError] = useState<string | null>(null);
  // Currently active specification section
  const [activeSection, setActiveSection] = useState<string>("overview");
  // Search query for filtering specification content
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchRvcSpec();
        setSpecData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    void loadData();
  }, []);

  // Placeholder sections for the specification
  const sections = [
    { id: "overview", name: "Overview" },
    { id: "dgns", name: "DGNs" },
    { id: "protocol", name: "Protocol" },
    { id: "messages", name: "Messages" },
    { id: "data_types", name: "Data Types" },
    { id: "instances", name: "Instances" }
  ];

  return (
    <div className="px-4 py-6 max-w-5xl mx-auto">
      <Card className="bg-[var(--color-bg)] border border-[var(--color-border)] shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <h1 className="text-2xl font-bold text-[var(--color-text)]">RV-C Protocol Specification</h1>
          <input
            type="search"
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-bg-muted)] px-3 py-2 text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            placeholder="Search specification..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            aria-label="Search RV-C specification"
          />
        </div>
        <nav className="flex flex-wrap gap-2 mb-4" aria-label="Specification sections">
          {sections.map(section => (
            <button
              key={section.id}
              className={`px-3 py-1 rounded-md font-medium transition-colors text-[var(--color-text)] ${activeSection === section.id ? "bg-[var(--color-primary)] text-white" : "bg-[var(--color-bg-muted)] hover:bg-[var(--color-primary)/10]"}`}
              style={{ border: "1px solid var(--color-border)" }}
              onClick={() => setActiveSection(section.id)}
              aria-current={activeSection === section.id ? "page" : undefined}
            >
              {section.name}
            </button>
          ))}
        </nav>
        {loading && <Loading className="my-8" />}
        {error && (
          <div className="text-red-600 bg-red-50 border border-red-200 rounded p-4 my-4" role="alert">
            Error loading specification: {error}
          </div>
        )}
        {!loading && !error && (
          <div className="min-h-[200px] text-[var(--color-text)]">
            {/* TODO: Render specData content by section and searchQuery */}
            <div className="italic text-[var(--color-muted)]">Section content coming soon.</div>
          </div>
        )}
      </Card>
    </div>
  );
}
