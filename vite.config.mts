import { parse, resolve } from "node:path";
import { glob } from "glob";
import { visualizer } from "rollup-plugin-visualizer";
import {
  type AliasOptions,
  defineConfig,
  type PluginOption,
  type Rollup,
  type UserConfig,
} from "vite";
import tsconfig from "./tsconfig.json";

const outDir = resolve(__dirname, "./staticfiles/generated/bundled");
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

export default defineConfig((config: UserConfig) => {
  return {
    base: "/static/bundled/",
    appType: "custom",
    build: {
      outDir: outDir,
      manifest: true, // goes into .vite/manifest.json in the build folder
      modulePreload: false, // would require `import 'vite/modulepreload-polyfill'` to always be injected
      emptyOutDir: config.mode === "production", // Avoid rebuilding everything in dev mode
      rollupOptions: {
        input: collectedFiles,
        output: {
          // Mirror architecture of static folders in generated .js and .css
          entryFileNames: (chunkInfo: Rollup.PreRenderedChunk) => {
            if (chunkInfo.facadeModuleId !== null) {
              return `${getRelativeAssetPath(chunkInfo.facadeModuleId)}.[hash].js`;
            }
            return "[name].[hash].js";
          },
          assetFileNames: (chunkInfo: Rollup.PreRenderedAsset) => {
            if (
              chunkInfo.names?.length === 1 &&
              chunkInfo.originalFileNames?.length === 1 &&
              collectedFiles.includes(chunkInfo.originalFileNames[0])
            ) {
              return `${getRelativeAssetPath(chunkInfo.originalFileNames[0])}.[hash][extname]`;
            }
            return "[name].[hash][extname]";
          },
          chunkFileNames: "[name].[hash].js",
        },
      },
    },
    resolve: {
      alias: getAliases(),
    },
    // biome-ignore lint/style/useNamingConvention: that's how it's called
    inject: { Alpine: "alpinejs", htmx: "htmx.org" },
    plugins: [visualizer({ filename: ".bundle-size-report.html" }) as PluginOption],
  } satisfies UserConfig;
});
