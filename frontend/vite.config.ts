import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  build: { rollupOptions: { input: { main: resolve(process.cwd(), "index.html"), forecasting: resolve(process.cwd(), "forecasting.html") } } }
});