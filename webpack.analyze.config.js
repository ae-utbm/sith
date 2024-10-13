// biome-ignore lint/correctness/noUndeclaredDependencies: webpack works with commonjs
const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin;
const config = require("./webpack.config.js");

module.exports = {
  ...config,
  plugins: [...config.plugins, new BundleAnalyzerPlugin()],
};
