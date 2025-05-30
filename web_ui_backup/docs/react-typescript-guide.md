# React 19 with TypeScript Style Guide

This document outlines the recommended patterns for React 19 with TypeScript in the rvc2api web_ui project. It serves as a reference for implementing consistent coding patterns across the codebase.

## Component Structure

### Functional Components with TypeScript

```tsx
import { useState } from "react";
import type { ReactNode } from "react";

interface ComponentProps {
  title: string;
  children?: ReactNode;
}

export function MyComponent({ title, children }: ComponentProps) {
  const [state, setState] = useState<string>("");

  return (
    <div>
      <h1>{title}</h1>
      {children}
    </div>
  );
}
```

### JSDoc Documentation

Components should be documented using JSDoc comments:

```tsx
/**
 * A component that displays a card with a title and content
 *
 * @param props - The component props
 * @returns A React component
 */
export function Card({ title, content }: CardProps) {
  // Component implementation
}
```

## Type Imports and Exports

### Import Types

Use `import type` for type-only imports to avoid including them in the bundle:

```tsx
// Correct
import type { MyType, AnotherType } from "./types";
import { someFunction } from "./utils";

// Avoid (unless needed for actual values)
import { MyType, AnotherType, someFunction } from "./utils";
```

### Export Types

Use `export type` for type-only exports:

```tsx
// In a file with only types
export type User = {
  id: string;
  name: string;
};

// In a barrel file with types
export type * from "./user-types";
```

## React 19 Best Practices

### Hooks

Use the latest hook patterns:

```tsx
// Effect with proper cleanup
useEffect(() => {
  const subscription = subscribe();

  // Return a cleanup function
  return () => {
    subscription.unsubscribe();
  };
}, [dependency]);

// TypeScript with useState
const [value, setValue] = useState<number | null>(null);
```

### Avoid `any` Type

Use `unknown` instead of `any` for better type safety:

```tsx
// Avoid
function processData(data: any) {
  // ...
}

// Prefer
function processData(data: unknown) {
  if (typeof data === "string") {
    // TypeScript knows data is a string here
  } else if (Array.isArray(data)) {
    // TypeScript knows data is an array here
  }
}
```

## JSDoc Guidelines

### Component Documentation

````tsx
/**
 * A component that displays user information
 *
 * @example
 * ```tsx
 * <UserProfile user={user} showAvatar={true} />
 * ```
 */
export function UserProfile({ user, showAvatar }: UserProfileProps) {
  // ...
}
````

### Interface Documentation

```tsx
/**
 * Represents a user in the system
 */
interface User {
  /** Unique identifier for the user */
  id: string;

  /** The user's display name */
  name: string;

  /** User's email address */
  email: string;

  /** When true, user has admin privileges */
  isAdmin?: boolean;
}
```

### Hook Documentation

```tsx
/**
 * Hook for managing form state
 *
 * @param initialValues - Initial form values
 * @returns Form state and handlers
 */
export function useForm<T extends Record<string, unknown>>(initialValues: T) {
  // ...
}
```

## Type Safety

### Discriminated Unions

Use discriminated unions for complex state:

```tsx
type FetchState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

function useFetchData<T>(): [FetchState<T>, () => Promise<void>] {
  const [state, setState] = useState<FetchState<T>>({ status: "idle" });
  // ...
}
```

### Type Guards

Use type guards for better type narrowing:

```tsx
function isApiResponse<T>(value: unknown): value is ApiResponse<T> {
  return typeof value === "object" && value !== null && "success" in value;
}
```

## ESLint Configuration

The project uses a custom ESLint configuration with:

- TypeScript ESLint for type checking
- React hooks rules
- JSDoc validation
- Type import/export consistency

Run `npm run lint` to check your code against these rules.

## React 19 Features

React 19 includes several new features that we can utilize:

- Better Suspense support
- Improved server components
- Enhanced types
- Better debugging capabilities

Refer to the React 19 documentation for more details on these features.

## Further Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [JSDoc Documentation](https://jsdoc.app/)
