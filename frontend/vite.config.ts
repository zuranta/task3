import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Override locally (e.g. `BACKEND_PORT=8001 npm run dev`) without changing
// the default everyone else gets.
const backendPort = process.env.BACKEND_PORT ?? "8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": `http://localhost:${backendPort}`,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
});
