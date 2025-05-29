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

  // Type guard for optional x/y coordinates
  function hasXY(node: unknown): node is { x: number; y: number } {
    return (
      typeof node === "object" &&
      node !== null &&
      typeof (node as Record<string, unknown>).x === "number" &&
      typeof (node as Record<string, unknown>).y === "number"
    );
  }

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
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Theme-adaptive background
    ctx.fillStyle =
      getComputedStyle(document.documentElement).getPropertyValue("--background") || "#fff";
    ctx.fillRect(0, 0, width, height);

    // Draw edges
    if (networkData.nodes && networkData.edges) {
      ctx.strokeStyle =
        getComputedStyle(document.documentElement).getPropertyValue("--border") || "#888";
      ctx.lineWidth = 2;
      networkData.edges.forEach((edge) => {
        const from = networkData.nodes?.find((n) => n.id === edge.source);
        const to = networkData.nodes?.find((n) => n.id === edge.target);
        if (
          from &&
          to &&
          typeof from.address === "number" &&
          typeof to.address === "number"
        ) {
          const fromX = hasXY(from)
            ? from.x
            : width / 2 + 200 * Math.cos((from.address / 256) * 2 * Math.PI);
          const fromY = hasXY(from)
            ? from.y
            : height / 2 + 200 * Math.sin((from.address / 256) * 2 * Math.PI);
          const toX = hasXY(to)
            ? to.x
            : width / 2 + 200 * Math.cos((to.address / 256) * 2 * Math.PI);
          const toY = hasXY(to)
            ? to.y
            : height / 2 + 200 * Math.sin((to.address / 256) * 2 * Math.PI);
          ctx.beginPath();
          ctx.moveTo(fromX, fromY);
          ctx.lineTo(toX, toY);
          ctx.stroke();
        }
      });

      // Draw nodes
      networkData.nodes.forEach((node) => {
        const x = hasXY(node)
          ? node.x
          : width / 2 + 200 * Math.cos((node.address / 256) * 2 * Math.PI);
        const y = hasXY(node)
          ? node.y
          : height / 2 + 200 * Math.sin((node.address / 256) * 2 * Math.PI);
        ctx.beginPath();
        ctx.arc(x, y, 24, 0, 2 * Math.PI);
        ctx.fillStyle = node.status === "active"
          ? getComputedStyle(document.documentElement).getPropertyValue("--primary") || "#2563eb"
          : getComputedStyle(document.documentElement).getPropertyValue("--muted") || "#d1d5db";
        ctx.fill();
        ctx.lineWidth = 3;
        ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--border") || "#888";
        ctx.stroke();

        // Node label
        ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--foreground") || "#111";
        ctx.font = "14px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(node.name || String(node.id), x, y + 28);
      });
    }
  }, [networkData]);

  return (
    <div className="px-4 py-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Network Map</h1>
      <Card className="p-4 bg-background dark:bg-background border border-border dark:border-border shadow-md">
        {loading && <Loading />}
        {error && <div className="text-error-600 dark:text-error-400">{error}</div>}
        <div className="flex justify-center items-center">
          <canvas
            ref={canvasRef}
            width={width}
            height={height}
            className="rounded-lg border border-border bg-background dark:bg-background"
            style={{ width: "100%", maxWidth: width, height }}
            aria-label="RV-C Network Topology"
          />
        </div>
      </Card>
    </div>
  );
}

export default NetworkMap;
