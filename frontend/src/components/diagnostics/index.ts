/**
 * Diagnostics Components Index
 *
 * Exports all diagnostic-related components for easy importing
 */

export { SystemHealthScore } from './SystemHealthScore';
export { DTCManager } from './DTCManager';

// Re-export types for convenience
export type { SystemHealthResponse, DiagnosticTroubleCode, DTCFilters } from '@/api/types';
