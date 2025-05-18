"use client";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { ReactNode, useState, useEffect } from 'react';

export function QueryProvider({ children }: { children: ReactNode }) {
  const [isMounted, setIsMounted] = useState(false);
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  }));

  // This ensures we only render the QueryClientProvider after mounting
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Don't render anything until we're on the client
  if (!isMounted) {
    return null;
  }

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
