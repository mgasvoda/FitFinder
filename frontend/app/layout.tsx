import '../styles/globals.css';
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { QueryProvider } from '../components/QueryProvider';

export const metadata: Metadata = {
  title: 'FitFinder',
  description: 'Find your perfect fit',
  // Viewport is now configured in viewport.ts
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
