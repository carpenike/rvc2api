# React Frontend Instructions

## Technology Stack

- **React 19.1.0** with TypeScript strict mode
- **Vite** for development and production builds
- **TailwindCSS** for styling with shadcn/ui component library
- **React Query (@tanstack/react-query)** for server state management
- **React Router DOM** for client-side routing
- **WebSocket** for real-time data synchronization

## Project Structure

### Component Organization
```
frontend/src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui base components
│   └── app-*.tsx       # Application-specific components
├── pages/              # Route-level page components
├── hooks/              # Custom React hooks
├── contexts/           # React Context providers
├── api/                # API client and types
└── lib/                # Utility functions
```

### Design System
- **Base Components**: shadcn/ui components in `components/ui/`
- **Theme System**: Dark/light mode with system preference detection
- **Responsive Design**: Mobile-first approach with Tailwind breakpoints
- **Accessibility**: WAI-ARIA compliant components

## Code Quality Requirements

### TypeScript Configuration
```bash
# Required before all commits
npm run typecheck
npm run lint
npm run lint:fix  # Auto-fix ESLint issues
```

### Standards
- **TypeScript**: Strict mode with project references
- **ESLint**: Flat config with React, TypeScript, and JSDoc plugins
- **Formatting Rules**:
  - No trailing commas: `comma-dangle: ["error", "never"]`
  - Double quotes: `quotes: ["error", "double"]`
  - Semicolons required: `semi: ["error", "always"]`
- **Import Aliases**: Use `@/` for `src/` imports

### Interface Requirements
```typescript
// All standalone interface files must have imports
import type { ReactNode } from "react";

export interface ComponentProps {
  children: ReactNode;
  className?: string;
}
```

## State Management Patterns

### React Query for Server State
```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";

// Query pattern
export function useEntities() {
  return useQuery({
    queryKey: ["entities"],
    queryFn: () => apiClient.getEntities(),
    staleTime: 30000
  });
}

// Mutation with optimistic updates
export function useControlEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiClient.controlEntity,
    onMutate: async (variables) => {
      // Optimistic update logic
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["entities"] });
    }
  });
}
```

### WebSocket Integration
```typescript
import { useContext, useEffect } from "react";
import { WebSocketContext } from "@/contexts/websocket-context";

export function useWebSocketData() {
  const { socket, isConnected } = useContext(WebSocketContext);

  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      // Handle real-time updates
    };

    socket.addEventListener("message", handleMessage);
    return () => socket.removeEventListener("message", handleMessage);
  }, [socket]);

  return { isConnected };
}
```

### React Context for UI State
```typescript
import { createContext, useContext, ReactNode } from "react";

interface ThemeContextType {
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
```

## API Integration Patterns

### REST API Client
```typescript
// Centralized API client
class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || "";
  }

  async getEntities(): Promise<Entity[]> {
    const response = await fetch(`${this.baseUrl}/api/entities`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  async controlEntity(id: string, command: EntityCommand): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/entities/${id}/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command)
    });

    if (!response.ok) {
      throw new Error(`Control failed: ${response.status}`);
    }
  }
}

export const apiClient = new ApiClient();
```

### WebSocket Connection
```typescript
export function createWebSocketConnection() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/entities`;

  const socket = new WebSocket(wsUrl);

  socket.onopen = () => console.log("WebSocket connected");
  socket.onclose = () => {
    console.log("WebSocket disconnected, reconnecting...");
    setTimeout(() => createWebSocketConnection(), 3000);
  };
  socket.onerror = (error) => console.error("WebSocket error:", error);

  return socket;
}
```

## Component Patterns

### shadcn/ui Component Usage
```typescript
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";

export function EntityCard({ entity }: { entity: Entity }) {
  const controlMutation = useControlEntity();

  const handleToggle = () => {
    controlMutation.mutate({
      entityId: entity.id,
      command: { command: "toggle" }
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{entity.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center space-x-2">
          <Switch
            checked={entity.state === "on"}
            onCheckedChange={handleToggle}
            disabled={controlMutation.isPending}
          />
          <span>{entity.state}</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Performance Optimization
```typescript
import { memo, useMemo } from "react";
import { VirtualizedTable } from "@/components/virtualized-table";

// Memoize expensive components
export const EntityList = memo(function EntityList({ entities }: Props) {
  const sortedEntities = useMemo(
    () => entities.sort((a, b) => a.name.localeCompare(b.name)),
    [entities]
  );

  return <VirtualizedTable data={sortedEntities} />;
});
```

## Testing Patterns

### Vitest Configuration
```typescript
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Test wrapper with providers
function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

describe("EntityCard", () => {
  it("toggles entity state on switch click", async () => {
    const mockEntity = { id: "1", name: "Light", state: "off" };

    render(<EntityCard entity={mockEntity} />, { wrapper: TestWrapper });

    const toggle = screen.getByRole("switch");
    fireEvent.click(toggle);

    expect(mockControlEntity).toHaveBeenCalledWith({
      entityId: "1",
      command: { command: "toggle" }
    });
  });
});
```

## Build and Development

### Development Server
```bash
cd frontend
npm run dev          # Start development server on :5173
npm run build        # Production build to dist/
npm run preview      # Preview production build
```

### Environment Configuration
```typescript
// Use environment variables with Vite
const config = {
  apiUrl: import.meta.env.VITE_API_URL || "http://localhost:8000",
  wsUrl: import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws",
  isDevelopment: import.meta.env.DEV
};
```

## MCP Tools for Frontend Development

### Always Use @context7 First
- **React Patterns**: `@context7 React useState with TypeScript generics`
- **Component Design**: `@context7 React functional component TypeScript props`
- **Hooks**: `@context7 React useEffect cleanup pattern`
- **State Management**: `@context7 React Query optimistic updates`

### Project Context
- **Find Components**: `@context7 existing component patterns`
- **API Integration**: `@context7 WebSocket message handling`
- **Styling**: `@context7 Tailwind responsive design patterns`

## Critical Requirements

- **Unified API**: Use `/api/entities` endpoints only, never separate patterns like `/api/lights`
- **Entity Commands**: Use standardized command structure for all entity control
- **Type Safety**: All API responses must have proper TypeScript types
- **Real-time Updates**: Implement optimistic updates with WebSocket synchronization
- **Accessibility**: Ensure all interactive elements are keyboard accessible
- **Performance**: Use virtualization for large data sets and proper memoization
