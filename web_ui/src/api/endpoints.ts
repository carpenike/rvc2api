/**
 * API endpoint functions for communicating with the rvc2api backend
 *
 * These functions handle the fetch requests to the various API endpoints
 * and provide proper error handling and type safety.
 */
import { handleApiResponse } from "./index";
import type {
    AllCanStats,
    AppHealth,
    CanMessage,
    DeviceMapping,
    LightStatus,
    NetworkMapData,
    RvcSpecData,
    UnknownPgn,
    UnmappedEntry
} from "./types";

/** Base URL for API requests */
const API_BASE = "/api";

// Common fetch options
const defaultOptions: RequestInit = {
  headers: {
    "Content-Type": "application/json"
  }
};

// Application health check
export async function fetchAppHealth(): Promise<AppHealth> {
  const response = await fetch(`${API_BASE}/health`, defaultOptions);
  return handleApiResponse<AppHealth>(response);
}

// CAN interface status
export async function fetchCanStatus(): Promise<AllCanStats> {
  const response = await fetch(`${API_BASE}/can/status`, defaultOptions);
  return handleApiResponse<AllCanStats>(response);
}

// Light control
export async function fetchLights(): Promise<LightStatus[]> {
  // Updated to use the correct backend endpoint and query param
  const response = await fetch(`${API_BASE}/entities?device_type=light`, defaultOptions);
  const data: unknown = await handleApiResponse(response);
  // Map backend fields to LightStatus interface
  const normalize = (item: Record<string, unknown>): LightStatus => {
    let brightness: number | undefined = undefined;
    const raw = item.raw as Record<string, unknown> | undefined;
    if (typeof item.brightness === "number") {
      brightness = item.brightness as number;
    } else if (raw && typeof raw.operating_status === "number") {
      brightness = Math.round(Math.max(0, Math.min(100, (raw.operating_status as number / 200) * 100)));
    }
    return {
      id: (item.id as string) || (item.entity_id as string) || "",
      name: (item.name as string) || (item.friendly_name as string) || (item.id as string) || (item.entity_id as string) || "Unknown",
      instance: (item.instance as number) ?? 0,
      zone: (item.zone as number) ?? 0,
      state: typeof item.state === "boolean" ? (item.state as boolean) : item.state === "on",
      type: (item.type as string) || (item.device_type as string) || "",
      location: (item.location as string) || (item.suggested_area as string) || "",
      last_updated: (item.last_updated as string) || "",
      brightness
    };
  };
  if (Array.isArray(data)) {
    return data.map(normalize);
  }
  if (data && typeof data === "object") {
    // If backend returns an object keyed by id, convert to array
    return Object.values(data as Record<string, unknown>).map(item => normalize(item as Record<string, unknown>));
  }
  return [];
}

export interface LightCommand {
  command: string;
  state?: string;
  brightness?: number;
  [key: string]: unknown;
}

export async function setLightState(
  id: string,
  command: LightCommand
): Promise<LightStatus> {
  // Updated to use the correct backend endpoint and method
  const response = await fetch(`${API_BASE}/entities/${id}/control`, {
    ...defaultOptions,
    method: "POST",
    body: JSON.stringify(command)
  });
  return handleApiResponse<LightStatus>(response);
}

export async function setAllLights(state: boolean): Promise<LightStatus[]> {
  // Fetch all lights, then set each one
  const lights = await fetchLights();
  const results: LightStatus[] = [];
  for (const light of lights) {
    try {
      const updated = await setLightState(light.id, { command: "set_state", state: state ? "on" : "off" });
      results.push(updated);
    } catch {
      // Optionally handle errors per light
    }
  }
  return results;
}

// Device mapping
export async function fetchDeviceMappings(): Promise<DeviceMapping[]> {
  const response = await fetch(`${API_BASE}/mappings/devices`, defaultOptions);
  return handleApiResponse<DeviceMapping[]>(response);
}

// CAN Sniffer
export async function fetchRecentCanMessages(
  limit = 100
): Promise<CanMessage[]> {
  const response = await fetch(
    `${API_BASE}/can/recent?limit=${limit}`,
    defaultOptions
  );
  return handleApiResponse<CanMessage[]>(response);
}

// Unmapped entries
export async function fetchUnmappedEntries(): Promise<UnmappedEntry[]> {
  const response = await fetch(`${API_BASE}/mappings/unmapped`, defaultOptions);
  return handleApiResponse<UnmappedEntry[]>(response);
}

// Unknown PGNs
export async function fetchUnknownPgns(): Promise<UnknownPgn[]> {
  const response = await fetch(
    `${API_BASE}/mappings/unknown-pgns`,
    defaultOptions
  );
  return handleApiResponse<UnknownPgn[]>(response);
}

// RVC Spec
export async function fetchRvcSpec(): Promise<RvcSpecData> {
  const response = await fetch(`${API_BASE}/spec`, defaultOptions);
  return handleApiResponse<RvcSpecData>(response);
}

// Network Map
export async function fetchNetworkMap(): Promise<NetworkMapData> {
  const response = await fetch(`${API_BASE}/network/map`, defaultOptions);
  return handleApiResponse<NetworkMapData>(response);
}
