import { useEffect, useRef, useState } from "react";
import { fetchNetworkMap } from "../api/endpoints";
import type { NetworkMapData } from "../api/types";
import { Card, Loading } from "../components";

/**
 * Network Map page component
 *
 * Visualizes the RV-C network topology showing connected devices
 * and their relationships using a canvas-based network diagram.
 *
 * @returns The NetworkMap page component
 */
export function NetworkMap() {
  /** Network topology data from the API */
  const [networkData, setNetworkData] = useState<NetworkMapData | null>(null);

  /** Loading state for the API call */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

  /** Reference to the canvas element for drawing the network map */
  const canvasRef = useRef<HTMLCanvasElement>(null);

  /** Dimensions for the network visualization */
  const width = 800;
  const height = 600;

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchNetworkMap();
        setNetworkData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }

    void loadData();
    // Refresh data every 2 minutes
    const interval = setInterval(() => {
      void loadData();
    }, 120000);
    return () => clearInterval(interval);
  }, []);

  // Draw network map when data changes
  useEffect(() => {
    if (!networkData || !canvasRef.current) return;

    // This is a placeholder for actual visualization logic
    // In a real implementation, you'd use a library like D3.js or custom canvas drawing
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Set background
    ctx.fillStyle = "#1E293B"; // rv-background color
    ctx.fillRect(0, 0, width, height);

    // Draw network nodes and connections
    if (networkData.nodes && networkData.edges) {
      // Draw placeholder message until actual visualization is implemented
      ctx.fillStyle = "#F8FAFC"; // rv-text color
      ctx.font = "24px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(
        "Network Visualization (Placeholder)",
        width / 2,
        height / 2 - 20
      );
      ctx.font = "16px sans-serif";
      ctx.fillText(
        "Actual implementation would use D3.js or similar",
        width / 2,
        height / 2 + 20
      );
      ctx.fillText(
        `${networkData.nodes.length} nodes and ${networkData.edges.length} connections detected`,
        width / 2,
        height / 2 + 50
      );
    }
  }, [networkData]);

  if (loading && !networkData) {
    return <Loading message="Loading network map data..." />;
  }

  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">Network Map</h1>

      {error && (
        <div className="bg-rv-error/20 text-rv-error p-4 rounded-xl mb-6">
          Error loading network map: {error}
        </div>
      )}

      <Card title="Network Visualization">
        <div className="flex justify-center">
          <canvas
            ref={canvasRef}
            width={width}
            height={height}
            className="border border-rv-surface/30 rounded-lg max-w-full"
          ></canvas>
        </div>
      </Card>

      <Card title="Network Statistics">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-rv-surface/30 rounded-lg">
            <h3 className="text-lg font-medium mb-2">Devices</h3>
            <p className="text-3xl font-bold text-rv-primary">
              {networkData?.nodes?.length || 0}
            </p>
            <p className="text-sm text-rv-text/70 mt-1">
              Total devices on network
            </p>
          </div>

          <div className="p-4 bg-rv-surface/30 rounded-lg">
            <h3 className="text-lg font-medium mb-2">Connections</h3>
            <p className="text-3xl font-bold text-rv-accent">
              {networkData?.edges?.length || 0}
            </p>
            <p className="text-sm text-rv-text/70 mt-1">Active data pathways</p>
          </div>

          <div className="p-4 bg-rv-surface/30 rounded-lg">
            <h3 className="text-lg font-medium mb-2">Status</h3>
            <p className="text-3xl font-bold text-rv-success">
              {networkData ? "Active" : "Unknown"}
            </p>
            <p className="text-sm text-rv-text/70 mt-1">Network availability</p>
          </div>
        </div>
      </Card>

      <div className="text-center text-sm text-rv-text/50 mt-8">
        <p>
          Note: This is a simplified network visualization. For detailed
          diagnostics, use the CAN Sniffer.
        </p>
        <p>
          Last updated:{" "}
          {networkData?.timestamp
            ? new Date(networkData.timestamp).toLocaleString()
            : "Never"}
        </p>
      </div>
    </section>
  );
}
