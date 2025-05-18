/**
 * API module exports
 *
 * This barrel file re-exports all API-related functions and types
 * from the individual modules for easier importing throughout the application.
 */
export * from "./docsApi";
export * from "./endpoints";
export type * from "./types";

/**
 * Helper for handling API responses with proper error handling
 *
 * @template T - The expected response data type
 * @param response - The fetch Response object
 * @returns A promise resolving to the typed response data
 * @throws Error if the response is not OK with status code and message
 */
export async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `API error: ${response.status}`);
  }
  return (await response.json()) as T;
}
