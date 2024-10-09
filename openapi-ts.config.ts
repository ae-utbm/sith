// biome-ignore lint/correctness/noNodejsModules: this only used at compile time
const path = require("node:path");
import { defineConfig } from "@hey-api/openapi-ts";

// biome-ignore lint/style/noDefaultExport: needed for openapi-ts
export default defineConfig({
  client: "@hey-api/client-fetch",
  input: path.resolve(__dirname, "./staticfiles/generated/openapi/schema.json"),
  output: path.resolve(__dirname, "./staticfiles/generated/openapi"),
});
