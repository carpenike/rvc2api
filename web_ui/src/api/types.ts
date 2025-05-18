/**
 * API type definitions
 * These types should match the backend Pydantic models
 */
export type * from "./additional-types";

/**
 * Generic API response wrapper
 *
 * @template T - The type of data in the success response
 */
export interface ApiResponse<T> {
  /** Whether the request was successful */
  success: boolean;

  /** The data returned by the API (present when success is true) */
  data?: T;

  /** Error message (present when success is false) */
  error?: string;
}

/**
 * Application health status information
 */
export interface AppHealth {
  /** Current health status of the application */
  status: "healthy" | "degraded" | "unhealthy";

  /** Application version */
  version: string;

  /** ISO timestamp of when the application started */
  startTime: string;

  /** Uptime in seconds */
  uptime: number;

  /** Whether the CAN bus connection is established */
  can_connected: boolean;
}

export interface CanStatus {
  interface_type: string;
  is_connected: boolean;
  status_message: string;
  statistics?: {
    messages_received: number;
    messages_sent: number;
    errors: number;
    last_message_timestamp?: string;
  };
}

export interface LightStatus {
  id: string;
  name: string;
  instance: number;
  zone: number;
  state: boolean;
  type: string;
  location?: string;
  last_updated: string;
}

export interface CanMessage {
  timestamp: string;
  dgn: number;
  source_address: number;
  destination_address?: number;
  priority: number;
  data: number[];
  decoded?: {
    name: string;
    fields: Record<string, unknown>;
    raw_data: string;
  };
}

export interface DeviceMapping {
  source_address: number;
  name?: string;
  device_type?: string;
  manufacturer?: string;
  function_instance?: number;
  status?: "active" | "inactive";
  last_seen?: string;
}
