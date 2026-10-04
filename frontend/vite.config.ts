import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, /api is proxied to the FastAPI server so the browser
// only ever talks to one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
});
