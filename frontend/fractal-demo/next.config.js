/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  transpilePackages: ['three', '@react-three/fiber', '@react-three/drei'],
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'three/examples/jsm': 'three/examples/jsm',
    };
    return config;
  },
  env: {
    SCALE_ENGINE_URL: process.env.SCALE_ENGINE_URL || 'http://localhost:3001',
    WEBSOCKET_URL: process.env.WEBSOCKET_URL || 'ws://localhost:3001',
  },
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig