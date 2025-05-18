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
  /** RV-C specification data from the API */
  /** RV-C specification data from the API */
  const [_specData, setSpecData] = useState<RvcSpecData | null>(null);

  /** Loading state for the API call */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

  /** Currently active specification section */
  const [activeSection, setActiveSection] = useState<string>("overview");

  /** Search query for filtering specification content */
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    /**
     * Loads specification data from the API
     */
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

  /**
   * Renders the appropriate content based on the current state
   *
   * @returns The rendered content for the active section
   */
  const renderContent = () => {
    if (loading) {
      return <Loading message="Loading RVC specification..." />;
    }

    if (error) {
      return (
        <div className="bg-rv-error/20 text-rv-error p-4 rounded-lg">
          Error loading specification: {error}
        </div>
      );
    }

    // If we have real data, we would use it here
    // For now, just show placeholder content
    return (
      <div className="py-4">
        <h2 className="text-xl font-bold mb-4 text-rv-primary">
          {sections.find((s) => s.id === activeSection)?.name || "Overview"}
        </h2>

        <div className="bg-rv-surface/20 p-8 rounded-lg text-center">
          <svg
            className="h-16 w-16 mx-auto text-rv-text/40"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="text-xl mt-4">
            RVC Specification Content Coming Soon
          </h3>
          <p className="mt-2 text-rv-text/70">
            This section will display detailed information about the{" "}
            {activeSection} from the RV-C specification.
          </p>
        </div>
      </div>
    );
  };

  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">RVC Specification</h1>

      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Search specification..."
            className="w-full p-3 pl-10 bg-rv-surface text-rv-text rounded-lg focus:ring-2 focus:ring-rv-primary focus:outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <svg
            className="absolute left-3 top-3.5 h-5 w-5 text-rv-text/50"
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
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Sidebar Navigation */}
        <div className="md:w-64 flex-shrink-0">
          <Card title="Sections">
            <nav className="flex flex-col">
              {sections.map((section) => (
                <button
                  key={section.id}
                  className={`text-left p-3 rounded-lg ${
                    activeSection === section.id
                      ? "bg-rv-primary/20 text-rv-primary"
                      : "hover:bg-rv-surface/60"
                  }`}
                  onClick={() => setActiveSection(section.id)}
                >
                  {section.name}
                </button>
              ))}
            </nav>
          </Card>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          <Card>{renderContent()}</Card>
        </div>
      </div>

      <div className="text-center text-sm text-rv-text/50 mt-6">
        <p>
          Note: This view is a placeholder. Full RV-C specification content is
          under development.
        </p>
      </div>
    </section>
  );
}
