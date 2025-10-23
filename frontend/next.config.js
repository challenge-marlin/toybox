const backendOrigin = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:4000';

const nextConfig = {
  async rewrites() {
    return [
      { source: '/api/:path*',     destination: `${backendOrigin}/api/:path*` },
      { source: '/uploads/:path*', destination: `${backendOrigin}/uploads/:path*` },
    ];
  },
};
module.exports = nextConfig;
