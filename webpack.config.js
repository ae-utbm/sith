const glob = require("glob");
// biome-ignore lint/correctness/noNodejsModules: this is backend side
const path = require("node:path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const TerserPlugin = require("terser-webpack-plugin");

module.exports = {
  entry: glob
    .sync("./!(static)/static/webpack/**/*?(-)index.[j|t]s?(x)")
    .reduce((obj, el) => {
      // We include the path inside the webpack folder in the name
      const relativePath = [];
      const fullPath = path.parse(el);
      for (const dir of fullPath.dir.split("/").reverse()) {
        if (dir === "webpack") {
          break;
        }
        relativePath.push(dir);
      }
      relativePath.push(fullPath.name);
      obj[relativePath.join("/")] = `./${el}`;
      return obj;
    }, {}),
  cache: {
    type: "filesystem", // This reduces typescript compilation time like crazy when you restart the server
  },
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "./staticfiles/generated/webpack"),
    clean: true,
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js"],
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
            // biome-ignore lint/style/useNamingConvention: this is how the underlying library wants it
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
            cacheDirectory: true,
          },
        },
      },
      {
        test: /\.js$/,
        enforce: "pre",
        use: ["source-map-loader"],
      },
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/,
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
