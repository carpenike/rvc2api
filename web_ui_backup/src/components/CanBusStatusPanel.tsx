import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
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
    return <p className="text-muted-foreground">No CAN interfaces found.</p>;
  }

  return (
    <Table aria-label="CAN bus interface status table">
      <TableCaption className="sr-only">CAN bus interface status</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Interface</TableHead>
          <TableHead>State</TableHead>
          <TableHead>Bitrate</TableHead>
          <TableHead>RX Packets</TableHead>
          <TableHead>TX Packets</TableHead>
          <TableHead>RX Errors</TableHead>
          <TableHead>TX Errors</TableHead>
          <TableHead>Bus Errors</TableHead>
          <TableHead>Restarts</TableHead>
          <TableHead>Notes</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Object.values(interfaces).map((iface) => (
          <TableRow key={iface.name}>
            <TableCell className="font-semibold">{iface.name}</TableCell>
            <TableCell>{iface.state ?? "-"}</TableCell>
            <TableCell>{iface.bitrate ?? "-"}</TableCell>
            <TableCell>{iface.rx_packets ?? "-"}</TableCell>
            <TableCell>{iface.tx_packets ?? "-"}</TableCell>
            <TableCell className="text-destructive">{iface.rx_errors ?? "-"}</TableCell>
            <TableCell className="text-destructive">{iface.tx_errors ?? "-"}</TableCell>
            <TableCell className="text-destructive">{iface.bus_errors ?? "-"}</TableCell>
            <TableCell className="text-warning">{iface.restarts ?? "-"}</TableCell>
            <TableCell className="text-muted-foreground">{iface.notes ?? "-"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
