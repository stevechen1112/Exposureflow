/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@exposureflow/ui", "@exposureflow/sdk", "@exposureflow/shared-types"],
};

module.exports = nextConfig;
