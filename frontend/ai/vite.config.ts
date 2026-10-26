import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/system': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/profile': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
});
