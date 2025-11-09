'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // Global defaults for better caching
        staleTime: 60 * 1000, // Data fresh for 1 minute
        gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
        retry: 2,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        refetchOnWindowFocus: true, // Refresh on tab focus
        refetchOnMount: false, // Don't refetch if data is fresh
        refetchOnReconnect: true, // Refetch on network reconnect
      },
      mutations: {
        retry: 1,
        retryDelay: 1000,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* React Query DevTools - only in development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom" />
      )}
    </QueryClientProvider>
  );
}
