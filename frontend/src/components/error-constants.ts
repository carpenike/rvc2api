/**
 * Error state constants and configurations
 */

export const ErrorConfig = {
  // Default error messages
  messages: {
    network: "Unable to connect to the server. Please check your network connection.",
    timeout: "Request timed out. Please try again.",
    server: "Server error occurred. Please try again later.",
    validation: "Invalid data provided. Please check your input.",
    notFound: "The requested resource was not found.",
    unauthorized: "You are not authorized to access this resource.",
    forbidden: "Access to this resource is forbidden.",
    generic: "An unexpected error occurred. Please try again."
  },

  // Error titles
  titles: {
    network: "Connection Error",
    timeout: "Timeout Error",
    server: "Server Error",
    validation: "Validation Error",
    notFound: "Not Found",
    unauthorized: "Unauthorized",
    forbidden: "Forbidden",
    generic: "Error"
  },

  // Retry configuration
  retry: {
    defaultDelay: 1000,
    maxAttempts: 3,
    backoffMultiplier: 2
  }
} as const;
