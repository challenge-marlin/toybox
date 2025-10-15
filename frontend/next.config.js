const nextConfig = {
  async rewrites() {
    return [
      { source: '/api/:path*',     destination: 'http://backend:4000/api/:path*' },
      { source: '/uploads/:path*', destination: 'http://backend:4000/uploads/:path*' },
    ];
  },
};
module.exports = nextConfig;
