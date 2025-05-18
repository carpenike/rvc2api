/**
 * Documentation search API functions for rvc2api
 *
 * This module provides typed functions for interacting with the documentation
 * search API endpoints.
 */
import { handleApiResponse } from "./index";

/** Base URL for documentation API requests */
const DOCS_API_BASE = "/api/docs";

/**
 * Search result interface from the documentation search API
 */
export interface SearchResult {
  content: string;
  metadata: {
    section: string;
    title: string;
    pages: number[];
  };
  section: string;
  title: string;
  pages: number[];
}

/**
 * Search status response from the documentation API
 */
export interface SearchStatus {
  vector_search: {
    available: boolean;
    status: "available" | "unavailable";
    index_path: string;
    embedding_model?: string;
    error?: string;
  };
}

/**
 * Fetch the status of the documentation search service
 *
 * @returns Promise resolving to the search status
 */
export async function fetchDocSearchStatus(): Promise<SearchStatus> {
  const response = await fetch(`${DOCS_API_BASE}/status`);
  return handleApiResponse<SearchStatus>(response);
}

/**
 * Search the RV-C documentation
 *
 * @param query - The search query
 * @param k - Number of results to return (defaults to 3)
 * @returns Promise resolving to an array of search results
 * @throws Error if search is unavailable or fails
 */
export async function searchDocumentation(
  query: string,
  k = 3
): Promise<SearchResult[]> {
  if (!query || query.trim().length < 3) {
    return [];
  }

  const url = `${DOCS_API_BASE}/search?query=${encodeURIComponent(query)}&k=${k}`;
  const response = await fetch(url);

  if (response.status === 503) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Documentation search service is unavailable");
  }

  return handleApiResponse<SearchResult[]>(response);
}
