/**
 * API endpoint functions for communicating with the rvc2api backend
 *
 * These functions handle the fetch requests to the various API endpoints
 * and provide proper error handling and type safety.
 */
import { handleApiResponse } from "./index";
import type {
    AppHealth,
    CanMessage,
    CanStatus,
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
export async function fetchCanStatus(): Promise<CanStatus> {
  const response = await fetch(`${API_BASE}/can/status`, defaultOptions);
  return handleApiResponse<CanStatus>(response);
}

// Light control
export async function fetchLights(): Promise<LightStatus[]> {
  // Updated to use the correct backend endpoint and query param
  const response = await fetch(`${API_BASE}/entities?device_type=light`, defaultOptions);
  return handleApiResponse<LightStatus[]>(response);
}

export async function setLightState(
  id: string,
  state: boolean
): Promise<LightStatus> {
  // Updated to use the correct backend endpoint and method
  const response = await fetch(`${API_BASE}/entities/${id}/control`, {
    ...defaultOptions,
    method: "POST",
    body: JSON.stringify({ state })
  });
  return handleApiResponse<LightStatus>(response);
}

export async function setAllLights(state: boolean): Promise<LightStatus[]> {
  // Fetch all lights, then set each one
  const lights = await fetchLights();
  const results: LightStatus[] = [];
  for (const light of lights) {
    try {
      const updated = await setLightState(light.id, state);
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
