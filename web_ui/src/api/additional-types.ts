/**
 * Additional API type definitions related to RV-C specific data structures
 */

/**
 * Represents an unmapped entry in the RV-C network
 * These are messages that have been received but don't match known device mappings
 */
export interface UnmappedEntry {
  /** Data Group Number (DGN) for the entry */
  dgn?: number;

  /** Source address of the device that sent the message */
  source_address?: number;

  /** CAN bus priority level */
  priority?: number;

  /** ISO timestamp when the message was received */
  timestamp?: string;

  /** Raw data bytes as an array of numbers */
  data?: number[];

  /** Structured representation of the raw message data */
  raw_data?: Record<string, unknown>;
}

/**
 * Represents an unknown Parameter Group Number (PGN) in the system
 * These are messages with PGNs that aren't defined in the RV-C specification
 */
export interface UnknownPgn {
  /** Parameter Group Number */
  pgn?: number;

  /** Unique identifier for the PGN entry */
  id?: string;

  /** ISO timestamp when this PGN was first observed */
  first_seen?: string;

  /** ISO timestamp when this PGN was most recently observed */
  last_seen?: string;

  /** Number of times this PGN has been observed */
  occurrence_count?: number;

  /** Example data from a message with this PGN */
  sample_data?: Record<string, unknown>;

  /** List of source addresses that have sent messages with this PGN */
  source_addresses?: number[];
}

export interface RvcSpecData {
  version?: string;
  last_updated?: string;
  sections?: Record<string, unknown>;
  dgns?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface NetworkMapData {
  timestamp?: string;
  nodes?: NetworkNode[];
  edges?: NetworkEdge[];
  statistics?: {
    active_devices: number;
    message_count: number;
    message_rate: number;
  };
}

export interface NetworkNode {
  id: string | number;
  type: string;
  address: number;
  name?: string;
  manufacturer?: string;
  device_type?: string;
  status: "active" | "inactive";
  last_seen?: string;
}

export interface NetworkEdge {
  source: string | number;
  target: string | number;
  message_count?: number;
  last_message?: string;
}
