import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Rewrote from: REF-MISSIONS（薄客户端直连 HTTP，无 BFF）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
