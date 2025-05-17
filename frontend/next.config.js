/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
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
