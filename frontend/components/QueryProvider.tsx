"use client";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { ReactNode, useState } from 'react';

export function QueryProvider({ children }: { children: ReactNode }) {
  // Ensure QueryClient is not recreated on every render
  const [queryClient] = useState(() => new QueryClient());
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
