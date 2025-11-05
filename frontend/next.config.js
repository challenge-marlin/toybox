// Determine backend origin only from explicit envs. If neither is set, avoid
// falling back to a hard-coded host in production to prevent misrouting.
const backendOrigin = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE || '';

const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost', port: '4000', pathname: '/uploads/**' },
      { protocol: 'https', hostname: 'api.toybox.example.com', pathname: '/uploads/**' },
    ],
  },
  async rewrites() {
    // If backendOrigin is not defined, do not set rewrites. This allows an
    // external reverse proxy (e.g. Caddy/Nginx) to handle /api and /uploads.
    if (!backendOrigin) return [];
    return [
      { source: '/api/:path*',     destination: `${backendOrigin}/api/:path*` },
      { source: '/uploads/:path*', destination: `${backendOrigin}/uploads/:path*` },
    ];
  },
};
module.exports = nextConfig;
