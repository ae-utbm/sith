const glob = require("glob");
const path = require("node:path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const TerserPlugin = require("terser-webpack-plugin");

module.exports = {
  entry: glob.sync("./!(static)/static/webpack/**?(-)index.js").reduce((obj, el) => {
    obj[path.parse(el).name] = `./${el}`;
    return obj;
  }, {}),
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "./staticfiles/generated/webpack"),
    clean: true,
  },
  plugins: [new MiniCssExtractPlugin()],
  optimization: {
    minimizer: [
      "...",
      new CssMinimizerPlugin({
        parallel: true,
      }),
      new TerserPlugin({
        parallel: true,
        terserOptions: {
          mangle: true,
          compress: {
            drop_console: true,
          },
        },
      }),
    ],
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        sideEffects: true,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
      },
      {
        test: /\.(jpe?g|png|gif)$/i,
        type: "asset/resource",
      },
      {
        test: /\.m?js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env"],
          },
        },
      },
      {
        test: /\.js$/,
        enforce: "pre",
        use: ["source-map-loader"],
      },
      {
        test: require.resolve("jquery"),
        loader: "expose-loader",
        options: {
          exposes: [
            {
              globalName: ["$"],
              override: true,
            },
            {
              globalName: ["jQuery"],
              override: true,
            },
            {
              globalName: ["window.jQuery"],
              override: true,
            },
          ],
        },
      },
    ],
  },
};
