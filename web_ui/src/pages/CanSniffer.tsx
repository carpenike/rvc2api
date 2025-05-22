import clsx from "clsx";
import { useCallback, useEffect, useState } from "react";
import { Button, Card } from "../components";

/**
 * CAN message interface representing a message on the CAN bus
 */
interface CanMessage {
  /** Timestamp when the message was received */
  time: string;

  /** Direction of the message: TX (transmitted) or RX (received) */
  dir: "TX" | "RX";

  /** Parameter Group Number in hexadecimal format */
  pgn: string;

  /** Data Group Number in hexadecimal format */
  dgn: string;

  /** Human-readable name of the message type if known */
  name: string;

  /** CAN arbitration ID in hexadecimal format */
  arb_id: string;

  /** Raw data bytes in hexadecimal format */
  data: string;

  /** Decoded message content if available */
  decoded: string;
}

/**
 * CAN Sniffer page component
 *
 * Provides a real-time view of messages on the RV-C CAN bus
 * with filtering, pause/resume functionality, and detailed message inspection.
 *
 * @returns The CanSniffer page component
 */
export function CanSniffer() {
  /** Collection of CAN messages to display */
  const [messages, setMessages] = useState<CanMessage[]>([]);

  /** Loading state for initial data fetch */
  const [loading, setLoading] = useState(true);

  /** Error state for failed operations */
  const [error, setError] = useState<string | null>(null);

  /** Whether live message updates are enabled */
  const [isLive, setIsLive] = useState(false);

  /** Current filter text */
  const [filter, setFilter] = useState("");

  const [messageLimit, setMessageLimit] = useState(100);

  const fetchMessages = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/can/sniffer");
      if (!response.ok) {
        throw new Error("Failed to fetch CAN sniffer data");
      }
      const data = await response.json();
      setMessages(data.slice(-messageLimit)); // Limit to prevent performance issues
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  }, [messageLimit]);

  useEffect(() => {
    void fetchMessages();
  }, [fetchMessages]);

  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      void fetchMessages();
    }, 2000);
    return () => clearInterval(interval);
  }, [isLive, fetchMessages]);

  const toggleLive = () => {
    setIsLive(prev => !prev);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const filteredMessages = filter
    ? messages.filter((msg) =>
        msg.name.toLowerCase().includes(filter.toLowerCase()) ||
        msg.pgn.toLowerCase().includes(filter.toLowerCase()) ||
        msg.dgn.toLowerCase().includes(filter.toLowerCase()) ||
        msg.arb_id.toLowerCase().includes(filter.toLowerCase())
      )
    : messages;

  const exportCSV = () => {
    const headers = Object.keys(filteredMessages[0] || {}).join(",");
    const rows = filteredMessages.map(msg =>
      Object.values(msg).map(val =>
        typeof val === "string" ? `"${val.replace(/"/g, "\"\"")}"` : val
      ).join(",")
    );

    const csv = [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `can-sniffer-export-${new Date().toISOString().slice(0, 19)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <main className="p-4 md:p-8 bg-rv-surface min-h-screen" aria-label="CAN Sniffer page">
      <Card className="max-w-6xl mx-auto bg-rv-surface shadow-md rounded-lg p-4 md:p-6">
        <header className="mb-4 flex flex-col md:flex-row md:items-center md:justify-between">
          <h1 className="text-2xl font-bold text-rv-text mb-2 md:mb-0" id="can-sniffer-heading">
            CAN Sniffer
          </h1>
          <div className="flex gap-2 items-center">
            <Button
              variant={isLive ? "primary" : "secondary"}
              aria-label={isLive ? "Pause live updates" : "Resume live updates"}
              onClick={toggleLive}
              data-testid="toggle-live-btn"
            >
              {isLive ? "Pause" : "Resume"}
            </Button>
            <Button
              variant="ghost"
              aria-label="Clear messages"
              onClick={clearMessages}
              data-testid="clear-btn"
            >
              Clear
            </Button>
            <Button
              variant="secondary"
              onClick={exportCSV}
              disabled={filteredMessages.length === 0}
              aria-label="Export messages to CSV"
              data-testid="export-csv-btn"
            >
              Export CSV
            </Button>
          </div>
        </header>
        <div className="mb-4 flex flex-col md:flex-row md:items-center gap-2">
          <label htmlFor="can-filter" className="text-rv-text font-medium">
            Filter:
          </label>
          <input
            id="can-filter"
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-rv-surface border border-rv-border rounded-md px-2 py-1 text-sm text-rv-text focus:outline-none focus:ring-2 focus:ring-rv-primary"
            placeholder="Name, PGN, DGN, or Arb ID"
            aria-label="Filter CAN messages"
            data-testid="filter-input"
          />
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-8" role="status" aria-live="polite" data-testid="loading-state">
            <span className="text-rv-text">Loading CAN messages…</span>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-8" role="alert" aria-live="assertive" data-testid="error-state">
            <span className="text-rv-error font-semibold">{error}</span>
          </div>
        ) : (
          <section aria-labelledby="can-sniffer-heading">
            <div className="overflow-x-auto rounded-md border border-rv-border bg-rv-surface">
              <table className="min-w-full text-sm text-rv-text" aria-label="CAN messages table" data-testid="can-table">
                <caption className="sr-only">CAN messages</caption>
                <thead className="bg-rv-muted">
                  <tr>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">Time</th>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">Dir</th>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">PGN</th>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">DGN</th>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">Name</th>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">Arb ID</th>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">Data</th>
                    <th scope="col" className="px-2 py-2 text-left font-semibold">Decoded</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMessages.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center text-rv-muted py-6" data-testid="no-messages-row">
                        No CAN messages to display.
                      </td>
                    </tr>
                  ) : (
                    filteredMessages.map((msg, i) => (
                      <tr
                        key={i}
                        className={clsx(i % 2 === 0 ? "bg-rv-surface" : "bg-rv-muted/50")}
                        data-testid="can-row"
                      >
                        <td className="px-2 py-1 whitespace-nowrap">{msg.time}</td>
                        <td className={clsx("px-2 py-1 font-mono", msg.dir === "TX" ? "text-rv-primary" : "text-rv-secondary")}>{msg.dir}</td>
                        <td className="px-2 py-1 font-mono">{msg.pgn}</td>
                        <td className="px-2 py-1 font-mono">{msg.dgn}</td>
                        <td className="px-2 py-1">{msg.name}</td>
                        <td className="px-2 py-1 font-mono">{msg.arb_id}</td>
                        <td className="px-2 py-1 font-mono">{msg.data}</td>
                        <td className="px-2 py-1">{msg.decoded}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}
        <div className="mt-4 flex justify-between items-center text-xs text-rv-text/60">
          <div>
            Showing {filteredMessages.length} of {messages.length} messages
            {filter && <span> (filtered)</span>}
          </div>
          <div className="flex items-center space-x-2">
            <label>Limit:</label>
            <select
              value={messageLimit}
              onChange={(e) => setMessageLimit(Number(e.target.value))}
              className="bg-rv-surface border border-rv-surface/80 text-rv-text rounded-lg px-2 py-1 text-xs"
            >
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="250">250</option>
              <option value="500">500</option>
              <option value="1000">1000</option>
            </select>
          </div>
        </div>
      </Card>
    </main>
  );
}
