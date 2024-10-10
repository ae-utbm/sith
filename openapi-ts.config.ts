// biome-ignore lint/correctness/noNodejsModules: this only used at compile time
import { resolve } from "node:path";
import { defineConfig } from "@hey-api/openapi-ts";

// biome-ignore lint/style/noDefaultExport: needed for openapi-ts
export default defineConfig({
  client: "@hey-api/client-fetch",
  input: resolve(__dirname, "./staticfiles/generated/openapi/schema.json"),
  output: resolve(__dirname, "./staticfiles/generated/openapi"),
});
