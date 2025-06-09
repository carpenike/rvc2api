---
mode: "agent"
description: "Design and prototype React UI components for CoachIQ"
tools: ["context7"]
---

# React UI Prototyping Guide

This guide helps you design and prototype React components for the CoachIQ web interface. Use this to plan the migration from static HTML to a modern React-based frontend.

---

## 1. Component Overview

### 1.1. Purpose

- What is the component's main responsibility?
- What user needs does it address?
- How does it integrate with the CoachIQ data model?

### 1.2. Component Scope

- What features should this component include?
- What should be excluded or handled by other components?
- What are the boundaries of its functionality?

---

## 2. Data Requirements

### 2.1. Props Interface

- What props does the component need?
- What validation should be applied to props?
- What default values are appropriate?

```typescript
interface DeviceCardProps {
  // Core device data
  deviceId: string;
  deviceName: string;
  deviceType: "tank" | "battery" | "thermostat" | "inverter" | string;
  status: "online" | "offline" | "error";

  // Optional configuration
  showDetailedView?: boolean;
  refreshInterval?: number; // milliseconds

  // Callback functions
  onStatusChange?: (deviceId: string, newStatus: string) => void;
  onSelect?: (deviceId: string) => void;
}
```

### 2.2. State Management

- What local state does the component need?
- What shared state should it access?
- How will updates be handled?

```typescript
// Local component state example
const [isExpanded, setIsExpanded] = useState(false);
const [deviceValues, setDeviceValues] = useState<DeviceValues>({});
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

// Global state access example (using React Context)
const { globalDevices, updateDevice } = useDeviceContext();
```

### 2.3. API Integration

- What API endpoints will this component use?
- What WebSocket events should it subscribe to?
- How will it handle loading states and errors?

```typescript
// API fetching example
useEffect(() => {
  const fetchDeviceData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/devices/${deviceId}`);
      if (!response.ok) throw new Error("Failed to fetch device data");
      const data = await response.json();
      setDeviceValues(data.values);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  fetchDeviceData();
  const interval = setInterval(fetchDeviceData, refreshInterval || 5000);
  return () => clearInterval(interval);
}, [deviceId, refreshInterval]);

// WebSocket example
useEffect(() => {
  const socket = new WebSocket("ws://localhost:8000/ws");

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.event === "device_update" && data.data.id === deviceId) {
      setDeviceValues(data.data.values);
    }
  };

  return () => socket.close();
}, [deviceId]);
```

---

## 3. UI Design

### 3.1. Component Structure

- What HTML structure will be used?
- What sub-components should be created?
- What component hierarchy will be established?

### 3.2. Styling Approach

- What CSS approach will be used (CSS modules, Tailwind, etc.)?
- What styling patterns should be followed?
- What responsive design considerations are needed?

```jsx
// Example component with Tailwind CSS
const DeviceCard = ({
  deviceId,
  deviceName,
  deviceType,
  status,
}: DeviceCardProps) => {
  // Component implementation
  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">{deviceName}</h3>
        <StatusBadge status={status} />
      </div>

      <div className="mt-2 text-sm text-gray-500">
        {deviceType.charAt(0).toUpperCase() + deviceType.slice(1)}
      </div>

      <div className="mt-4 border-t pt-3">
        <DeviceValuesList deviceId={deviceId} />
      </div>

      <button
        className="mt-3 w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        onClick={() => onSelect?.(deviceId)}
      >
        View Details
      </button>
    </div>
  );
};
```

### 3.3. Accessibility

- What ARIA attributes are needed?
- How will keyboard navigation be handled?
- What color contrast requirements should be met?

---

## 4. Interaction Design

### 4.1. User Interactions

- What actions can the user take?
- How will the component respond to user input?
- What feedback will be provided?

### 4.2. State Transitions

- What states can the component be in (loading, error, empty, etc.)?
- How will transitions between states be handled?
- What conditional rendering is needed?

```jsx
// State transitions example
return (
  <div className="device-card">
    {isLoading && <LoadingSpinner />}

    {!isLoading && error && (
      <ErrorDisplay message={error} retryAction={() => fetchDeviceData()} />
    )}

    {!isLoading && !error && Object.keys(deviceValues).length === 0 && (
      <EmptyState message="No data available for this device" />
    )}

    {!isLoading && !error && Object.keys(deviceValues).length > 0 && (
      <DeviceDetails
        values={deviceValues}
        isExpanded={isExpanded}
        onToggleExpand={() => setIsExpanded(!isExpanded)}
      />
    )}
  </div>
);
```

### 4.3. Error Handling

- How will API errors be displayed?
- What fallback UI will be shown when data is unavailable?
- How can users recover from errors?

---

## 5. Component Implementation

### 5.1. Component Code

- Provide the full React component implementation
- Include all necessary imports
- Add comments explaining key logic

```tsx
import React, { useState, useEffect } from "react";
import { StatusBadge } from "./StatusBadge";
import { DeviceValuesList } from "./DeviceValuesList";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { ErrorDisplay } from "../common/ErrorDisplay";
import { EmptyState } from "../common/EmptyState";
import { useDeviceData } from "../../hooks/useDeviceData";
import type { DeviceValues } from "../../types";

export interface DeviceCardProps {
  deviceId: string;
  deviceName: string;
  deviceType: string;
  status: "online" | "offline" | "error";
  showDetailedView?: boolean;
  refreshInterval?: number;
  onStatusChange?: (deviceId: string, newStatus: string) => void;
  onSelect?: (deviceId: string) => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({
  deviceId,
  deviceName,
  deviceType,
  status,
  showDetailedView = false,
  refreshInterval = 5000,
  onStatusChange,
  onSelect,
}) => {
  const [isExpanded, setIsExpanded] = useState(showDetailedView);

  // Custom hook for fetching device data
  const {
    data: deviceValues,
    isLoading,
    error,
    refetch,
  } = useDeviceData(deviceId, refreshInterval);

  // Notify parent component of status changes
  useEffect(() => {
    if (status !== prevStatus.current) {
      prevStatus.current = status;
      onStatusChange?.(deviceId, status);
    }
  }, [deviceId, status, onStatusChange]);

  // Status reference for comparison
  const prevStatus = React.useRef(status);

  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">{deviceName}</h3>
        <StatusBadge status={status} />
      </div>

      <div className="mt-2 text-sm text-gray-500">
        {deviceType.charAt(0).toUpperCase() + deviceType.slice(1)}
      </div>

      <div className="mt-4 border-t pt-3">
        {isLoading && <LoadingSpinner size="small" />}

        {!isLoading && error && (
          <ErrorDisplay
            message="Failed to load device data"
            retryAction={refetch}
          />
        )}

        {!isLoading && !error && (
          <DeviceValuesList values={deviceValues} isExpanded={isExpanded} />
        )}
      </div>

      <div className="mt-3 flex space-x-2">
        <button
          className="flex-1 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          {isExpanded ? "Show Less" : "Show More"}
        </button>

        <button
          className="flex-1 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          onClick={() => onSelect?.(deviceId)}
        >
          View Details
        </button>
      </div>
    </div>
  );
};
```

### 5.2. Custom Hooks

- Create any custom hooks needed by the component
- Explain their purpose and usage
- Include proper TypeScript typing

```tsx
// Custom hook for fetching device data
import { useState, useEffect, useCallback } from "react";
import type { DeviceValues } from "../types";

export function useDeviceData(
  deviceId: string,
  refreshInterval: number = 5000
) {
  const [data, setData] = useState<DeviceValues>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!deviceId) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/devices/${deviceId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch device data: ${response.statusText}`);
      }
      const result = await response.json();
      setData(result.values || {});
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsLoading(false);
    }
  }, [deviceId]);

  // Initial fetch and interval setup
  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  return { data, isLoading, error, refetch: fetchData };
}
```

### 5.3. Testing Strategy

- What unit tests should be written?
- What user interactions should be tested?
- What mock data is needed?

```tsx
// Example test for DeviceCard component
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { DeviceCard } from "./DeviceCard";
import { useDeviceData } from "../../hooks/useDeviceData";

// Mock the custom hook
jest.mock("../../hooks/useDeviceData");

describe("DeviceCard", () => {
  const mockDeviceData = {
    temperature: 72.5,
    humidity: 35,
    battery: 98,
  };

  beforeEach(() => {
    (useDeviceData as jest.Mock).mockReturnValue({
      data: mockDeviceData,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });
  });

  it("renders device information correctly", () => {
    render(
      <DeviceCard
        deviceId="thermostat_1"
        deviceName="Main Thermostat"
        deviceType="thermostat"
        status="online"
      />
    );

    expect(screen.getByText("Main Thermostat")).toBeInTheDocument();
    expect(screen.getByText("Thermostat")).toBeInTheDocument();
    expect(screen.getByText("72.5")).toBeInTheDocument();
  });

  it("expands and collapses when toggle button is clicked", () => {
    render(
      <DeviceCard
        deviceId="thermostat_1"
        deviceName="Main Thermostat"
        deviceType="thermostat"
        status="online"
      />
    );

    // Initially not all values may be visible
    expect(screen.queryByText("humidity")).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByText("Show More"));
    expect(screen.getByText("humidity")).toBeInTheDocument();
    expect(screen.getByText("35")).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(screen.getByText("Show Less"));
    expect(screen.queryByText("humidity")).not.toBeInTheDocument();
  });

  it("calls onSelect when View Details button is clicked", () => {
    const handleSelect = jest.fn();

    render(
      <DeviceCard
        deviceId="thermostat_1"
        deviceName="Main Thermostat"
        deviceType="thermostat"
        status="online"
        onSelect={handleSelect}
      />
    );

    fireEvent.click(screen.getByText("View Details"));
    expect(handleSelect).toHaveBeenCalledWith("thermostat_1");
  });

  it("displays loading state", () => {
    (useDeviceData as jest.Mock).mockReturnValue({
      data: {},
      isLoading: true,
      error: null,
      refetch: jest.fn(),
    });

    render(
      <DeviceCard
        deviceId="thermostat_1"
        deviceName="Main Thermostat"
        deviceType="thermostat"
        status="online"
      />
    );

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("displays error state and allows retry", () => {
    const mockRefetch = jest.fn();

    (useDeviceData as jest.Mock).mockReturnValue({
      data: {},
      isLoading: false,
      error: new Error("Failed to fetch data"),
      refetch: mockRefetch,
    });

    render(
      <DeviceCard
        deviceId="thermostat_1"
        deviceName="Main Thermostat"
        deviceType="thermostat"
        status="online"
      />
    );

    expect(screen.getByText("Failed to load device data")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Retry"));
    expect(mockRefetch).toHaveBeenCalled();
  });
});
```

---

## 6. Component Integration

### 6.1. Parent Components

- How will this component be used in parent components?
- What context or state management is needed at a higher level?
- How will it interact with siblings or related components?

### 6.2. WebSocket Integration

- How will the component subscribe to real-time updates?
- How will WebSocket reconnection be handled?
- How will message parsing and state updates be implemented?

### 6.3. API Integration

- How will the component fetch initial data?
- How will pagination or infinite scrolling be implemented if needed?
- What caching strategy should be used?

---

## 7. Performance Considerations

### 7.1. Rendering Optimization

- How will unnecessary re-renders be prevented?
- What memoization techniques should be used?
- What virtual list rendering is needed for large datasets?

### 7.2. Data Efficiency

- How will data fetching be optimized?
- What data should be cached locally?
- How will redundant API calls be prevented?

---

## 8. Development Checklist

### 8.1. Implementation Tasks

- [ ] Create component scaffold
- [ ] Implement data fetching logic
- [ ] Create UI elements
- [ ] Implement interactions
- [ ] Add error handling
- [ ] Optimize performance

### 8.2. Testing Tasks

- [ ] Create unit tests
- [ ] Test loading states
- [ ] Test error states
- [ ] Test user interactions
- [ ] Test with realistic data volumes
- [ ] Test performance

### 8.3. Documentation Tasks

- [ ] Document props interface
- [ ] Document usage examples
- [ ] Document integration patterns

---

## Output

Once this component design and prototype is complete, save it to `/docs/specs/react-<component-name>.md` where `<component-name>` is a kebab-case name descriptive of the component (e.g., `react-device-card.md` or `react-dashboard-layout.md`). This document will serve as the blueprint for implementation and can be shared with the development team.

---

This guide serves as a template for designing and implementing React components for the CoachIQ web interface. Adjust sections as needed based on the specific requirements of your component.
