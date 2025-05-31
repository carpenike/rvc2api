/**
 * Query Provider Component
 *
 * Provides React Query context to the application.
 * Includes development tools integration and global configuration.
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import type { ReactNode } from 'react';
import { createQueryClient } from '../../lib/query-client';

interface QueryProviderProps {
  children: ReactNode;
}

// Create a singleton query client instance
const queryClient = createQueryClient();

/**
 * Provides React Query context to the application
 */
export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Only show devtools in development */}
      {import.meta.env.DEV && (
        <ReactQueryDevtools
          initialIsOpen={false}
          buttonPosition="bottom-left"
        />
      )}
    </QueryClientProvider>
  );
}
