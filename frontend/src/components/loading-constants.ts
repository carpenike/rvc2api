/**
 * Loading state constants and configurations
 */

export const LoadingConfig = {
  // Default timing configurations
  debounceMs: 300,
  fadeInDuration: 200,
  spinnerSize: 24,

  // Default counts for skeleton loaders
  defaultCardCount: 6,
  defaultColumns: 3,

  // Loading messages
  messages: {
    connecting: "Connecting to server...",
    loading: "Loading...",
    syncing: "Syncing data...",
    failed: "Failed to load",
    retry: "Retry",
    offline: "You are offline"
  }
} as const;

export const LoadingVariants = {
  spinner: "spinner",
  skeleton: "skeleton",
  pulse: "pulse",
  fade: "fade"
} as const;

export type LoadingVariant = typeof LoadingVariants[keyof typeof LoadingVariants];
