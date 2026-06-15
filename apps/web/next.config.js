/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: process.env.SKIP_TYPECHECK === "true",
  },
  eslint: {
    ignoreDuringBuilds: process.env.SKIP_TYPECHECK === "true",
  },
  transpilePackages: ["@exposureflow/ui", "@exposureflow/sdk", "@exposureflow/shared-types"],
};

module.exports = nextConfig;
