import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths(), react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      "/chat": "http://127.0.0.1:5000",
      "/providers": "http://127.0.0.1:5000",
      "/conversations": "http://127.0.0.1:5000",
      "/memory": "http://127.0.0.1:5000",
      "/confirm": "http://127.0.0.1:5000",
      "/tools": "http://127.0.0.1:5000",
      "/images": "http://127.0.0.1:5000",
      "/health": "http://127.0.0.1:5000",
      "/code": "http://127.0.0.1:5000",
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
