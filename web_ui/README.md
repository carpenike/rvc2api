# RV-C2API Frontend

Modern React frontend for the RV-C2API system built with Vite, TypeScript, and Shadcn/UI.

## Tech Stack

- **React 18** - Modern React with concurrent features
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Shadcn/UI** - Modern, accessible component library
- **TailwindCSS v4** - Utility-first CSS framework
- **React Query** - Data fetching and state management
- **React Router** - Client-side routing

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm run test

# Run type checking
npm run typecheck

# Run linting
npm run lint
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests with Vitest
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors
- `npm run typecheck` - Run TypeScript checks

## Project Structure

```
src/
├── api/              # API clients and types
├── components/       # Reusable components
│   ├── ui/          # Shadcn/UI components
│   └── ...
├── hooks/           # Custom React hooks
├── lib/             # Utility libraries
├── pages/           # Page components
├── test/            # Test setup and utilities
└── types/           # TypeScript type definitions
```

## Component Guidelines

### Using Shadcn/UI Components

Always prefer Shadcn/UI components over custom implementations:

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Good
<Button variant="primary">Click me</Button>;

// Avoid custom button implementations
```

### Layout Consistency

All pages should use the `AppLayout` wrapper:

```tsx
import { AppLayout } from "@/components/app-layout";

export function MyPage() {
  return <AppLayout pageTitle="My Page">{/* Page content */}</AppLayout>;
}
```

### Accessibility

- Use semantic HTML elements
- Include proper ARIA attributes
- Test with keyboard navigation
- Ensure proper color contrast

## Testing

Tests are written with Vitest and React Testing Library:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

describe("MyComponent", () => {
  it("renders correctly", () => {
    render(<MyComponent />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });
});
```

## Performance

### Code Splitting

- Vendor libraries are automatically split into separate chunks
- Routes are lazy-loaded where appropriate
- Icon libraries use tree-shaking

### Build Optimization

- TypeScript compilation with strict mode
- ESLint with accessibility rules
- Vite optimizations for production builds

## Contributing

1. Follow the established patterns
2. Write tests for new components
3. Ensure accessibility compliance
4. Run linting and type checking before committing
   ...tseslint.configs.stylisticTypeChecked,
   ],
   languageOptions: {
   // other options...
   parserOptions: {
   project: ['./tsconfig.node.json', './tsconfig.app.json'],
   tsconfigRootDir: import.meta.dirname,
   },
   },
   })

````

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config({
  plugins: {
    // Add the react-x and react-dom plugins
    'react-x': reactX,
    'react-dom': reactDom,
  },
  rules: {
    // other rules...
    // Enable its recommended typescript rules
    ...reactX.configs['recommended-typescript'].rules,
    ...reactDom.configs.recommended.rules,
  },
})
````
