const backendOrigin = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:4000';

const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost', port: '4000', pathname: '/uploads/**' },
      { protocol: 'https', hostname: 'api.toybox.example.com', pathname: '/uploads/**' },
    ],
  },
  async rewrites() {
    return [
      { source: '/api/:path*',     destination: `${backendOrigin}/api/:path*` },
      { source: '/uploads/:path*', destination: `${backendOrigin}/uploads/:path*` },
    ];
  },
};
module.exports = nextConfig;
