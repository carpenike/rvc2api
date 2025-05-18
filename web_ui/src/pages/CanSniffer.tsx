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

  /** Field to apply the filter against */
  const [filterField, setFilterField] = useState<keyof CanMessage>("name");
  const [autoScroll, setAutoScroll] = useState(true);
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

  /**
   * Scrolls the message container to the bottom
   * Used for auto-scrolling when new messages arrive
   */
  const scrollToBottom = useCallback(() => {
    const container = document.getElementById("can-messages-container");
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, []);

  // Call scrollToBottom when messages change, if auto-scroll is enabled
  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [messages, autoScroll, scrollToBottom]);

  /**
   * Toggles live message updates on/off
   */
  const toggleLive = () => {
    setIsLive(prev => !prev);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const filteredMessages = messages.filter(msg => {
    if (!filter) return true;
    const value = msg[filterField]?.toString().toLowerCase() || "";
    return value.includes(filter.toLowerCase());
  });

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
    <section className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">CAN Sniffer</h1>
        <div className="space-x-2">
          <Button
            variant={isLive ? "primary" : "ghost"}
            onClick={toggleLive}
          >
            {isLive ? "Live • Stop" : "Start Live Feed"}
          </Button>
          <Button
            variant="ghost"
            onClick={clearMessages}
          >
            Clear
          </Button>
          <Button
            variant="secondary"
            onClick={exportCSV}
            disabled={filteredMessages.length === 0}
          >
            Export CSV
          </Button>
        </div>
      </div>

      <Card>
        <div className="mb-4 flex flex-wrap gap-2 items-center">
          <div className="flex items-center space-x-2">
            <label htmlFor="filter-field" className="text-sm">Filter by:</label>
            <select
              id="filter-field"
              value={filterField}
              onChange={(e) => setFilterField(e.target.value as keyof CanMessage)}
              className="bg-rv-surface border border-rv-surface/80 text-rv-text rounded-lg px-2 py-1 text-sm"
            >
              <option value="pgn">PGN</option>
              <option value="dgn">DGN</option>
              <option value="name">Name</option>
              <option value="arb_id">Arb ID</option>
              <option value="dir">Direction</option>
            </select>
          </div>
          <div className="flex-grow">
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder={`Filter by ${filterField}...`}
              className="bg-rv-surface border border-rv-surface/80 text-rv-text rounded-lg px-3 py-1 w-full"
            />
          </div>
          <label className="inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={() => setAutoScroll(prev => !prev)}
              className="sr-only peer"
            />
            <div className="relative w-9 h-5 bg-rv-surface/50 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-rv-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-rv-primary"></div>
            <span className="ms-3 text-sm font-medium text-gray-300">Auto-scroll</span>
          </label>
        </div>

        {loading && messages.length === 0 && (
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-rv-primary"></div>
          </div>
        )}

        {error && (
          <div className="bg-rv-error/20 p-4 rounded-lg border border-rv-error/30 text-rv-text">
            <p className="font-semibold">Error loading CAN messages</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {!loading && filteredMessages.length === 0 && !error && (
          <p className="text-rv-text/70 py-4 text-center">No CAN messages found.</p>
        )}

        {filteredMessages.length > 0 && (
          <div className="rounded-lg border border-rv-surface overflow-hidden">
            <div
              className="overflow-x-auto overflow-y-auto max-h-[60vh]"
              id="can-messages-container"
            >
              <table className="min-w-full divide-y divide-rv-surface/80">
                <thead className="bg-rv-surface/70 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      Dir
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      PGN
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      DGN
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      Arb ID
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      Data
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-rv-text/70 uppercase tracking-wider">
                      Decoded
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-rv-background/20 divide-y divide-rv-surface/40">
                  {filteredMessages.map((msg, index) => (
                    <tr
                      key={index}
                      className={`text-xs hover:bg-rv-surface/20 transition-colors ${
                        msg.dir === "TX" ? "text-rv-primary/80" : ""
                      }`}
                    >
                      <td className="px-3 py-2 whitespace-nowrap font-mono">{msg.time}</td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          msg.dir === "TX"
                            ? "bg-rv-success/20 text-rv-success"
                            : "bg-rv-primary/20 text-rv-primary"
                        }`}>
                          {msg.dir}
                        </span>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap font-mono">{msg.pgn}</td>
                      <td className="px-3 py-2 whitespace-nowrap font-mono">{msg.dgn}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{msg.name}</td>
                      <td className="px-3 py-2 whitespace-nowrap font-mono">{msg.arb_id}</td>
                      <td className="px-3 py-2 whitespace-nowrap font-mono">{msg.data}</td>
                      <td className="px-3 py-2 break-all font-mono max-w-sm">{msg.decoded}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
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
    </section>
  );
}
