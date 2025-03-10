// biome-ignore lint/correctness/noNodejsModules: this only used at compile time
import { resolve } from "node:path";
import { defineConfig } from "@hey-api/openapi-ts";

// biome-ignore lint/style/noDefaultExport: needed for openapi-ts
export default defineConfig({
  input: resolve(__dirname, "./staticfiles/generated/openapi/schema.json"),
  output: {
    path: resolve(__dirname, "./staticfiles/generated/openapi/client"),
  },
  plugins: [
    {
      name: "@hey-api/client-fetch",
      baseUrl: false,
      runtimeConfigPath: "./openapi-csrf.ts",
      exportFromIndex: true,
    },
  ],
});
