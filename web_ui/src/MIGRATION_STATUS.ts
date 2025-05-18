// This file is used to communicate the status of the React UI refactoring
// to future developers working on the project.

export type MigrationStatus = "complete" | "in-progress" | "not-started";

export interface MigrationItem {
  name: string;
  status: MigrationStatus;
  notes?: string;
}

export const migrationStatus = {
  core: [
    {
      name: "Project scaffolding",
      status: "complete",
      notes: "React app with Vite, TypeScript, and Tailwind CSS set up"
    },
    {
      name: "Component library",
      status: "complete",
      notes: "Basic UI components created (Button, Card, Toggle, etc.)"
    },
    {
      name: "Routing",
      status: "complete",
      notes: "React Router implemented with all required routes"
    },
    {
      name: "WebSocket connection",
      status: "complete",
      notes: "Real-time data connection with reconnection logic"
    },
    {
      name: "API integration",
      status: "complete",
      notes: "API client for backend communication"
    },
    {
      name: "Styling & theme",
      status: "complete",
      notes: "TailwindCSS with custom RV-themed colors"
    },
    {
      name: "Testing",
      status: "in-progress",
      notes: "Basic test setup complete, more tests needed"
    }
  ],
  pages: [
    { name: "Dashboard", status: "complete" },
    { name: "Lights", status: "complete" },
    { name: "CAN Sniffer", status: "complete" },
    { name: "Device Mapping", status: "complete" },
    {
      name: "Network Map",
      status: "complete",
      notes: "Basic implementation, visualization needs improvement"
    },
    {
      name: "RVC Spec",
      status: "complete",
      notes: "Placeholder implementation, needs real content"
    },
    { name: "Unmapped Entries", status: "complete" },
    { name: "Unknown PGNs", status: "complete" }
  ],
  features: [
    { name: "Dark theme", status: "complete" },
    { name: "Responsive design", status: "complete" },
    { name: "Error handling", status: "complete" },
    { name: "Loading states", status: "complete" },
    {
      name: "Light/dark mode toggle",
      status: "not-started",
      notes: "Currently dark mode only"
    },
    {
      name: "Data visualization",
      status: "in-progress",
      notes: "Basic visualizations implemented, more advanced charts needed"
    },
    {
      name: "User preferences",
      status: "not-started",
      notes: "No persistent user preferences yet"
    },
    {
      name: "Offline mode",
      status: "not-started",
      notes: "No offline capability implemented"
    }
  ]
};

export const nextSteps = [
  "Improve test coverage for all components",
  "Enhance RVC Spec viewer with real specification content",
  "Implement more advanced network visualization in Network Map",
  "Create light/dark theme toggle",
  "Implement user preference storage",
  "Optimize bundle size and performance",
  "Add more accessible keyboard navigation",
  "Create developer documentation for the frontend architecture"
];

/**
 * Progress calculation
 *
 * This gives a rough estimate of the migration progress by counting completed items
 */
const calculateProgress = () => {
  const allItems = [
    ...migrationStatus.core,
    ...migrationStatus.pages,
    ...migrationStatus.features
  ];

  const completed = allItems.filter(
    (item) => item.status === "complete"
  ).length;
  const total = allItems.length;

  return {
    completed,
    total,
    percentage: Math.round((completed / total) * 100)
  };
};

export const migrationProgress = calculateProgress();
