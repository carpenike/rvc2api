import React from "react";

interface CanInterfaceStats {
  name: string;
  state?: string | null;
  bitrate?: number | null;
  sample_point?: number | null;
  tx_packets?: number | null;
  rx_packets?: number | null;
  tx_bytes?: number | null;
  rx_bytes?: number | null;
  tx_errors?: number | null;
  rx_errors?: number | null;
  bus_errors?: number | null;
  restarts?: number | null;
  notes?: string | null;
}

interface CanBusStatusPanelProps {
  interfaces: Record<string, CanInterfaceStats>;
}

export const CanBusStatusPanel: React.FC<CanBusStatusPanelProps> = ({ interfaces }) => {
  if (!interfaces || Object.keys(interfaces).length === 0) {
    return <p className="text-rv-text/50">No CAN interfaces found.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table
        className="min-w-full bg-rv-surface/80 rounded-lg shadow text-sm border border-rv-surface/30"
        aria-label="CAN bus interface status table"
      >
        <caption className="sr-only">CAN bus interface status</caption>
        <thead>
          <tr className="text-rv-text/70 border-b border-rv-surface/30">
            <th scope="col" className="px-4 py-2 text-left">Interface</th>
            <th scope="col" className="px-4 py-2 text-left">State</th>
            <th scope="col" className="px-4 py-2 text-left">Bitrate</th>
            <th scope="col" className="px-4 py-2 text-left">RX Packets</th>
            <th scope="col" className="px-4 py-2 text-left">TX Packets</th>
            <th scope="col" className="px-4 py-2 text-left">RX Errors</th>
            <th scope="col" className="px-4 py-2 text-left">TX Errors</th>
            <th scope="col" className="px-4 py-2 text-left">Bus Errors</th>
            <th scope="col" className="px-4 py-2 text-left">Restarts</th>
            <th scope="col" className="px-4 py-2 text-left">Notes</th>
          </tr>
        </thead>
        <tbody>
          {Object.values(interfaces).map((iface, idx) => (
            <tr
              key={iface.name}
              className={[
                "border-b border-rv-surface/20 hover:bg-rv-background/10",
                idx % 2 === 0 ? "bg-rv-surface/60" : "bg-transparent"
              ].join(" ")}
            >
              <td className="px-4 py-2 font-semibold text-rv-text">{iface.name}</td>
              <td className="px-4 py-2 text-rv-text/90">{iface.state ?? "-"}</td>
              <td className="px-4 py-2 text-rv-text/90">{iface.bitrate ?? "-"}</td>
              <td className="px-4 py-2 text-rv-text/90">{iface.rx_packets ?? "-"}</td>
              <td className="px-4 py-2 text-rv-text/90">{iface.tx_packets ?? "-"}</td>
              <td className="px-4 py-2 text-rv-error/80">{iface.rx_errors ?? "-"}</td>
              <td className="px-4 py-2 text-rv-error/80">{iface.tx_errors ?? "-"}</td>
              <td className="px-4 py-2 text-rv-error/80">{iface.bus_errors ?? "-"}</td>
              <td className="px-4 py-2 text-rv-warning/80">{iface.restarts ?? "-"}</td>
              <td className="px-4 py-2 text-rv-text/80">{iface.notes ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
