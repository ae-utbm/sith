// biome-ignore lint/correctness/noNodejsModules: this is backend side
import { parse, resolve } from "node:path";
import inject from "@rollup/plugin-inject";
import { glob } from "glob";
import type { AliasOptions, UserConfig } from "vite";
import type { Rollup } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";
import tsconfig from "./tsconfig.json";

const outDir = resolve(__dirname, "./staticfiles/generated/bundled");
const vendored = resolve(outDir, "vendored");
const nodeModules = resolve(__dirname, "node_modules");
const collectedFiles = glob.sync(
  "./!(static)/static/bundled/**/*?(-)index.?(m)[j|t]s?(x)",
);

/**
 * Grabs import aliases from tsconfig for #module: imports
 **/
function getAliases(): AliasOptions {
  const aliases: AliasOptions = {};
  for (const [key, value] of Object.entries(tsconfig.compilerOptions.paths)) {
    aliases[key] = resolve(__dirname, value[0]);
  }
  return aliases;
}

/**
 * Helper function that finds the relative path of an index.js/ts file in django static folders
 **/
function getRelativeAssetPath(path: string): string {
  let relativePath: string[] = [];
  const fullPath = parse(path);
  for (const dir of fullPath.dir.split("/").reverse()) {
    if (dir === "bundled") {
      break;
    }
    relativePath.push(dir);
  }
  // We collected folders in reverse order, we put them back in the original order
  relativePath = relativePath.reverse();
  relativePath.push(fullPath.name);
  return relativePath.join("/");
}

// biome-ignore lint/style/noDefaultExport: this is recommended by documentation
export default {
  base: "/static/bundled/",
  appType: "custom",
  build: {
    outDir: outDir,
    modulePreload: false, // would require `import 'vite/modulepreload-polyfill'` to always be injected
    emptyOutDir: true,
    rollupOptions: {
      input: collectedFiles,
      output: {
        // Mirror architecture of static folders in generated .js and .css
        entryFileNames: (chunkInfo: Rollup.PreRenderedChunk) => {
          if (chunkInfo.facadeModuleId !== null) {
            return `${getRelativeAssetPath(chunkInfo.facadeModuleId)}.js`;
          }
          return "[name].js";
        },
        assetFileNames: (chunkInfo: Rollup.PreRenderedAsset) => {
          if (
            chunkInfo.names?.length === 1 &&
            chunkInfo.originalFileNames?.length === 1 &&
            collectedFiles.includes(chunkInfo.originalFileNames[0])
          ) {
            return (
              getRelativeAssetPath(chunkInfo.originalFileNames[0]) +
              parse(chunkInfo.names[0]).ext
            );
          }
          return "[name].[ext]";
        },
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