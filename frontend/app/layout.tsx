import '../styles/globals.css';
import type { ReactNode } from 'react';
import { QueryProvider } from '../components/QueryProvider';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
