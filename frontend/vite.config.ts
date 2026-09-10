import { defineConfig } from "vite";
import { resolve } from "node:path";

// Builds panel and Lovelace cards into a single self-contained bundle.
// The output is committed so HACS ships it without a Node toolchain.
// No runtime dependency may be external: Lit is compiled into the bundle.
export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/main.ts"),
      formats: ["es"],
      fileName: () => "ev-charging.js",
    },
    outDir: resolve(__dirname, "../custom_components/ev_charging/frontend"),
    emptyOutDir: false,
    rollupOptions: {
      external: [],
    },
    target: "es2022",
    minify: "esbuild",
    sourcemap: false,
  },
});
