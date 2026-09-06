import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Anchor to this file's directory, not the invocation cwd: pnpm workspace runs
// and UNC-mapped drives otherwise resolve the root inconsistently.
const webRoot = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(webRoot, "src"),
    },
  },

  test: {
    root: webRoot,
    include: ["src/**/*.test.{ts,tsx}"],
    exclude: ["tests/e2e/**", "node_modules/**"],
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80,
      },
    },
  },
});
