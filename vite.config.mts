// biome-ignore lint/correctness/noNodejsModules: this is backend side
import { parse, resolve } from "node:path";
import inject from "@rollup/plugin-inject";
import { glob } from "glob";
import type { AliasOptions, UserConfig } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";
import tsconfig from "./tsconfig.json";

const outDir = resolve(__dirname, "./staticfiles/generated/bundled");
const vendored = resolve(outDir, "vendored");
const nodeModules = resolve(__dirname, "node_modules");

function getAliases(): AliasOptions {
  const aliases: AliasOptions = {};
  for (const [key, value] of Object.entries(tsconfig.compilerOptions.paths)) {
    aliases[key] = resolve(__dirname, value[0]);
  }
  return aliases;
}

type IndexPath = { [find: string]: string };

// biome-ignore lint/style/noDefaultExport: this is recommended by documentation
export default {
  base: "/static/bundled/",
  appType: "custom",
  build: {
    outDir: outDir,
    modulePreload: false, // would require `import 'vite/modulepreload-polyfill'` to always be injected
    emptyOutDir: true,
    rollupOptions: {
      input: glob
        .sync("./!(static)/static/bundled/**/*?(-)index.?(m)[j|t]s?(x)")
        .reduce((obj: IndexPath, el) => {
          // We include the path inside the bundled folder in the name
          let relativePath: string[] = [];
          const fullPath = parse(el);
          for (const dir of fullPath.dir.split("/").reverse()) {
            if (dir === "bundled") {
              break;
            }
            relativePath.push(dir);
          }
          // We collected folders in reverse order, we put them back in the original order
          relativePath = relativePath.reverse();
          relativePath.push(fullPath.name);
          obj[relativePath.join("/")] = `./${el}`;
          return obj;
        }, {}),
      output: {
        entryFileNames: "[name].js",
        assetFileNames: "[name].[ext]",
      },
    },
  },
  resolve: {
    alias: getAliases(),
  },

  plugins: [
    inject({
      // biome-ignore lint/style/useNamingConvention: that's how it's called
      Alpine: "alpinejs",
    }),
    viteStaticCopy({
      targets: [
        {
          src: resolve(nodeModules, "jquery/dist/jquery.min.js"),
          dest: vendored,
        },
        {
          src: resolve(nodeModules, "jquery-ui/dist/jquery-ui.min.js"),
          dest: vendored,
        },
        {
          src: resolve(nodeModules, "jquery.shorten/src/jquery.shorten.min.js"),
          dest: vendored,
        },
      ],
    }),
  ],
  optimizeDeps: {
    include: ["jquery"],
  },
} satisfies UserConfig;
