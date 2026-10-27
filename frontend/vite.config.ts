import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { readdirSync } from "node:fs";

const htmlPages = readdirSync(process.cwd())
  .filter((name) => name.endsWith(".html"));

const input = Object.fromEntries(
  htmlPages.map((page) => [page.replace(/\.html$/, ""), resolve(process.cwd(), page)])
);

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  build: { rollupOptions: { input } }
});
