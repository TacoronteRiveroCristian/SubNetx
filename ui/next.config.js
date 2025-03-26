/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // Add API proxy configuration to handle CORS issues
    async rewrites() {
      return [
        {
          // Rewrite API requests to the target container
          source: '/api/targets',
          destination: 'http://subnetx_vpn:8000/targets',
        },
        {
          // Rewrite API requests for latest targets data
          source: '/api/targets/latest',
          destination: 'http://subnetx_vpn:8000/targets/latest',
        },
      ];
    },
  };

  module.exports = nextConfig;
