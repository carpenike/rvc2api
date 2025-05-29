import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import toast from "react-hot-toast";
import type { EntitiesResponse, Entity } from "../useEntities";
import { useEntities, useEntity, useEntityControl, useLights } from "../useEntities";

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Test data
const mockEntity: Entity = {
  entity_id: "light.living_room",
  device_type: "light",
  friendly_name: "Living Room Light",
  state: "on",
  suggested_area: "living_room",
  capabilities: ["brightness", "toggle"],
  groups: ["lights", "main_floor"],
  brightness: 80,
  last_updated: "2025-05-28T10:00:00Z",
  raw: {}
};

const mockEntitiesResponse: EntitiesResponse = {
  "light.living_room": mockEntity,
  "light.bedroom": {
    ...mockEntity,
    entity_id: "light.bedroom",
    friendly_name: "Bedroom Light",
    state: "off",
    brightness: 0
  }
};

// Helper to create wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false
      }
    }
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("useEntities", () => {
  beforeEach(() => {
    mockFetch.mockClear();
    (toast.success as jest.Mock).mockClear();
    (toast.error as jest.Mock).mockClear();
  });

  it("fetches entities successfully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockEntitiesResponse
    });

    const { result } = renderHook(() => useEntities(), {
      wrapper: createWrapper()
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockEntitiesResponse);
    expect(mockFetch).toHaveBeenCalledWith("/api/entities");
  });

  it("handles fetch error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useEntities(), {
      wrapper: createWrapper()
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });

  it("fetches entities with filters", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockEntitiesResponse
    });

    const { result } = renderHook(
      () => useEntities({ device_type: "light", area: "living_room" }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/entities?device_type=light&area=living_room"
    );
  });
});

describe("useEntity", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  it("fetches single entity successfully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockEntity
    });

    const { result } = renderHook(
      () => useEntity("light.living_room"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockEntity);
    expect(mockFetch).toHaveBeenCalledWith("/api/entities/light.living_room");
  });

  it("skips fetch when entityId is not provided", () => {
    const { result } = renderHook(
      () => useEntity(""),
      { wrapper: createWrapper() }
    );

    expect(result.current.data).toBeUndefined();
    expect(mockFetch).not.toHaveBeenCalled();
  });
});

describe("useEntityControl", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  it("controls entity successfully", async () => {
    const mockResponse = { success: true, entity: mockEntity };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const { result } = renderHook(() => useEntityControl(), {
      wrapper: createWrapper()
    });

    await result.current.mutateAsync({
      entityId: "light.living_room",
      command: { command: "turn_on" }
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/entities/light.living_room/control",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: "turn_on" })
      })
    );

    expect(toast.success).toHaveBeenCalledWith("Entity control successful");
  });

  it("handles control error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Control failed"));

    const { result } = renderHook(() => useEntityControl(), {
      wrapper: createWrapper()
    });

    try {
      await result.current.mutateAsync({
        entityId: "light.living_room",
        command: { command: "turn_on" }
      });
    } catch {
      // Expected to throw
    }

    expect(toast.error).toHaveBeenCalledWith("Failed to control entity: Control failed");
  });
});

describe("useLights", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  it("fetches only light entities", async () => {
    const lightEntities = {
      "light.living_room": mockEntity,
      "light.bedroom": { ...mockEntity, entity_id: "light.bedroom" }
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => lightEntities
    });

    const { result } = renderHook(() => useLights(), {
      wrapper: createWrapper()
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockFetch).toHaveBeenCalledWith("/api/entities?device_type=light");
    expect(result.current.data).toEqual(lightEntities);
  });

  it("applies additional filters to light entities", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockEntitiesResponse
    });

    const { result } = renderHook(
      () => useLights("living_room"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/entities?device_type=light&area=living_room"
    );
  });
});
