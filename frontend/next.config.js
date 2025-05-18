/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keep static export for now, but consider using 'standalone' if you need runtime env vars
  output: 'export',
  
  // Environment variables that should be available at runtime
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_KEY: process.env.NEXT_PUBLIC_API_KEY,
  },
  
  images: {
    unoptimized: true,
  },
  // Configure page extensions to include .page.jsx and .page.tsx
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
  
  // Disable server-side rendering for API routes
  experimental: {
    // Enable the App Router
    appDir: true,
    // Disable server components for static export
    serverComponents: false,
  },
  // Only enable rewrites in development
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    }
    return [];
  },
  // Disable TypeScript type checking during build
  typescript: {
    ignoreBuildErrors: true,
  },
  // Disable ESLint during build
  eslint: {
    ignoreDuringBuilds: true,
  },
};

// Remove rewrites for production build
if (process.env.NODE_ENV === 'production') {
  delete nextConfig.rewrites;
}

module.exports = nextConfig;
